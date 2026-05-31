#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import random
import base64
import argparse
from datetime import date
from io import BytesIO
from pathlib import Path
from PIL import Image
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from _retry import RetryableError, retry

load_dotenv()

try:
    from supabase import create_client
except ImportError:
    create_client = None

MAX_WORKERS = 5

API_KEY = os.environ.get("OPENROUTER_API_KEY")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")
_supabase_client = None

MODEL = "google/gemini-2.5-flash"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

INPUTS_DIR = Path("inputs")
OUTPUTS_DIR = Path("outputs")

MAX_LONG_SIDE = 1024
JPEG_QUALITY = 90
JITTER_MIN = 0.5
JITTER_MAX = 2.0
MAX_RETRIES = 5
REQUEST_TIMEOUT = 30

# Ghost file tracking: { student_id: { "image": filename, "closest_match": {...}, "text_name": "..." } }
GHOST_STUDENTS: dict[str, dict] = {}


def get_supabase_client():
    global _supabase_client
    if _supabase_client is None and create_client and SUPABASE_URL and SUPABASE_KEY:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def lookup_student_info(student_id: str) -> dict:
    """Look up student name and class from Supabase classlists table.
    Returns dict with 'name' and 'class' keys (may be empty strings)."""
    client = get_supabase_client()
    if not client:
        return {"name": "", "class": ""}
    try:
        result = client.table("classlists") \
            .select("name, class") \
            .eq("student_id", student_id) \
            .execute()
        if result.data:
            row = result.data[0]
            return {"name": row.get("name", ""), "class": row.get("class", "")}
    except Exception:
        pass
    return {"name": "", "class": ""}


_classlist_cache = None


def load_classlist_cache():
    """Fetch all student IDs and names from classlists into a module-level cache.
    Returns dict mapping student_id -> {name, class}."""
    global _classlist_cache
    if _classlist_cache is not None:
        return _classlist_cache
    _classlist_cache = {}
    client = get_supabase_client()
    if not client:
        return _classlist_cache
    try:
        result = client.table("classlists") \
            .select("student_id, name, class") \
            .execute()
        for row in (result.data or []):
            sid = row.get("student_id", "")
            if sid:
                _classlist_cache[sid] = {
                    "name": row.get("name", ""),
                    "class": row.get("class", ""),
                }
    except Exception:
        pass
    return _classlist_cache


def find_closest_student_id(target_id: str) -> dict | None:
    """Given a student ID not found in the classlist, find the numerically
    closest known ID and return {id, name, class, distance}. Returns None
    if no candidates exist or target_id is not numeric."""
    if not target_id.isdigit():
        return None
    cache = load_classlist_cache()
    if not cache:
        return None
    target_num = int(target_id)
    best = None
    best_dist = 10_000_000
    for known_id, info in cache.items():
        if known_id.isdigit():
            dist = abs(int(known_id) - target_num)
            if dist < best_dist:
                best_dist = dist
                best = {
                    "id": known_id,
                    "name": info["name"],
                    "class": info["class"],
                    "distance": dist,
                }
    # Only suggest if within a reasonable range (avoid random matches)
    if best and best["distance"] <= 100:
        return best
    return None


def heuristic_extract_name(text: str) -> str:
    """Attempt to extract a student name from transcribed text using
    common self-introduction patterns. Returns the name or empty string."""
    import re
    patterns = [
        r"my name is (\w+)",
        r"my name's (\w+)",
        r"i'm (\w+)",
        r"i am (\w+)",
        r"i am called (\w+)",
        r"i'm called (\w+)",
        r"this is (\w+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1)
            name = raw.capitalize()
            if len(name) >= 2:
                return name
    return ""


SYSTEM_PROMPT = """CRITICAL RULE — READ TWICE: Transcribe ONLY handwriting that physically exists on the page. ZERO invented content. If the page has blank space, handwriting ends, or the text trails off — you MUST stop. Do NOT continue the student's essay. Do NOT start a new topic. Do NOT write "I went to..." or "I also..." or any continuation. Empty space means nothing to transcribe. Returning empty text is better than guessing.

You are a handwriting transcription tool. Your task is to transcribe handwritten English essays EXACTLY as written — preserve ALL spelling, grammar, and vocabulary errors. You are a transcriber, NOT a proofreader. Do not correct anything.

Rules:
1. Extract the 5-digit student ID from the ID field on the page. Do NOT include the ID field, class label, or any demographic header text in the student_text output.
2. Transcribe ONLY the handwriting on the ruled lines beneath the demographic block. Skip the student ID/class/name header area entirely.
3. CRITICAL: Insert \\n ONLY at paragraph boundaries. NEVER insert \\n at handwritten line endings. A handwritten line ending is just a page-width wrap, not a paragraph break. The entire page should be transcribed as a single flowing block with \\n only where the writer intended a new paragraph (indentation, blank line, topic change). A letter's salutation ("Dear X,") and closing ("Sincerely," / "See you soon!") are distinct paragraphs; separate them with \\n.
4. NEVER wrap lines at a fixed character width. Each paragraph reads as one continuous line with no \\n except at paragraph boundaries. If the output has a \\n at every handwritten line, you are doing it WRONG.
5. Do NOT render crossed-out or deleted text. Skip it entirely.
6. Do NOT render any drawings, illustrations, doodles, emoji, or decorations (e.g. smiley faces, hearts, stars, apples, flowers). Skip them entirely. They are not part of the written text.
7. If the writer used carats (^) or other insertion symbols, insert those words at their intended position so the natural flow of the passage is retained.

Return ONLY a valid JSON object with exactly these keys:
{"student_id": "5-digit number", "student_text": "the transcribed text"}

PARAGRAPH BREAKS: Use \\n\\n (double newline) in student_text to separate paragraphs.
Example of correct output with two paragraphs:
{"student_id": "12345", "student_text": "First paragraph ends here.\\n\\nSecond paragraph starts on a new line. This paragraph continues."}

REMEMBER: \\n must ONLY appear at paragraph boundaries (indentation, blank line, topic change). Never at handwritten line wraps. Every handwritten line ending should flow into the next word without \\n.
REMEMBER: The student_text must contain ONLY the essay writing. Do not include any part of the student ID, class, or name fields printed at the top of the page.

No markdown, no code fences, no explanation — raw JSON only."""


def find_input_folders():
    if not INPUTS_DIR.exists():
        return []
    return sorted([d for d in INPUTS_DIR.iterdir() if d.is_dir()])


def show_menu(folders):
    print("\nAvailable input folders:")
    for i, f in enumerate(folders, 1):
        print(f"  {i}. {f.name}")
    while True:
        try:
            choice = input(f"\nSelect folder (1-{len(folders)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(folders):
                return folders[idx]
        except ValueError:
            pass
        print(f"Invalid choice. Enter a number 1-{len(folders)}.")


def ask_page_count():
    while True:
        try:
            count = input("How many image pages per essay? (1, 2, 3, 4+): ").strip()
            n = int(count.replace("+", ""))
            if n >= 1:
                return n
        except ValueError:
            pass
        print("Enter a positive number (e.g. 1, 2, 3, 4).")


def group_images(folder, pages_per_essay):
    """Group images sequentially into essays of `pages_per_essay` pages each.

    All image files in the folder are sorted alphabetically and grouped
    into sequential chunks. The student ID is extracted by the vision model
    from the page image, not from the filename.
    """
    image_files = sorted([
        f for f in folder.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    ])

    result = []
    for i in range(0, len(image_files), pages_per_essay):
        chunk = image_files[i:i + pages_per_essay]
        temp_id = f"essay-{(i // pages_per_essay) + 1:04d}"
        result.append({"student_id": temp_id, "pages": chunk})
        if len(chunk) < pages_per_essay:
            print(f"  Note: final group has {len(chunk)} page(s), expected {pages_per_essay}")

    return result


def preprocess_image(image_path):
    img = Image.open(image_path)
    img = img.convert("L")
    img.thumbnail((MAX_LONG_SIDE, MAX_LONG_SIDE), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


@retry(max_retries=MAX_RETRIES)
def call_openrouter(data_url):
    if not API_KEY:
        print("  Error: OPENROUTER_API_KEY not set")
        return None
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe this image verbatim. Return JSON with student_id and student_text."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"].strip()

        parsed = try_parse_json(content)
        if parsed:
            return parsed

        print(f"  Warning: could not parse model response as JSON. Raw: {content[:200]}")
        return None

    except requests.exceptions.HTTPError as e:
        status = r.status_code
        if status in (429, 502, 503):
            raise RetryableError(f"Rate limit/server error ({status})")
        print(f"  Error: HTTP {status} — {e}")
        return None
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise RetryableError(f"Connection error: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"  Error: unexpected API response — {e}")
        return None


def try_parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def jitter():
    time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))


def process_student_group(group, folder_name):
    student_id = group["student_id"]
    page_paths = group["pages"]
    print(f"\n  Processing student {student_id} ({len(page_paths)} pages)...")

    time.sleep(random.uniform(0, JITTER_MIN))

    page_texts = []
    extracted_id = None

    for idx, page_path in enumerate(page_paths, 1):
        print(f"    Page {idx}: {page_path.name}")
        try:
            data_url = preprocess_image(page_path)
        except Exception as e:
            print(f"    Error preprocessing {page_path.name}: {e}")
            continue

        result = call_openrouter(data_url)
        if result is None:
            print(f"    Failed to transcribe page {page_path.name}")
            continue

        sid = (result.get("student_id") or "").strip()
        text = (result.get("student_text") or "").strip()
        # Normalize literal \n sequences to actual newlines (the model outputs
        # these when it intends a paragraph break or line wrap in the JSON)
        text = text.replace("\\n", "\n")
        # Collapse single newlines (handwritten line wraps) into spaces.
        # Keep multi-newline runs (\n\n) as paragraph breaks.
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  # single \n → space
        text = re.sub(r'\n+', '\n\n', text)            # multi \n → double (parbreak)
        # Squash runs of spaces within each paragraph, preserve newlines
        parts = text.split("\n")
        parts = [" ".join(p.split()) for p in parts]
        text = "\n".join(parts)

        if idx == 1:
            extracted_id = sid if len(sid) == 5 else None
            if not extracted_id:
                print(f"    Warning: could not extract valid 5-digit student ID from page 1 (got '{sid}')")

        # Page 2+ never has a student ID written on it — ignore the model's
        # student_id for continuation pages and just use page 1's ID.
        if idx > 1 and extracted_id and sid != extracted_id and len(sid) == 5:
            print(f"    Warning: page {idx} returned different 5-digit ID '{sid}' (page 1 had '{extracted_id}') — text kept but ID possibly hallucinated")

        if text:
            page_texts.append(text)
        else:
            print(f"    Warning: page {idx} returned empty text")

        jitter()

    if not page_texts:
        print(f"  No text transcribed for {student_id}, skipping.")
        return None

    combined_text = " ".join(page_texts)
    final_id = extracted_id or student_id
    word_count = len(combined_text.split())

    # Look up student name and class from Supabase
    student_info = lookup_student_info(final_id)
    if student_info["name"]:
        print(f"    Found student: {student_info['name']} ({student_info['class']})")
    else:
        ghost_entry = {"image": page_paths[0].name if page_paths else "unknown"}
        # Try ID-based closest match (catch OCR misreads)
        match = find_closest_student_id(final_id)
        if match:
            print(f"    Student {final_id} not in classlist — closest match: {match['id']} ({match['name']}, dist={match['distance']})")
            ghost_entry["closest_match"] = match
        # Try text-based name extraction (catch missing Supabase entry)
        text_name = heuristic_extract_name(combined_text)
        if text_name:
            if match:
                print(f"    Text also suggests name '{text_name}'")
            else:
                print(f"    Student {final_id} not in classlist — text suggests name '{text_name}'")
            ghost_entry["text_name"] = text_name
        if match:
            student_info["name"] = f"{match['name']}? (closest ID {match['id']})"
            student_info["class"] = match["class"]
        elif text_name:
            student_info["name"] = text_name
            # Extract class from folder name (e.g. "M3-3A-assignment-2" → "M3-3A")
            m = re.match(r'([MUS]\d-\d[A-Za-z]+)', folder_name)
            student_info["class"] = m.group(1) if m else folder_name
        else:
            print(f"    Student {final_id} not in classlist (M3 cohort or unknown)")
        # Track this ghost with class for the report
        ghost_entry["class"] = student_info.get("class") or folder_name
        GHOST_STUDENTS[final_id] = ghost_entry

    output = {
        "student_id": final_id,
        "student_text": combined_text,
        "word_count": word_count,
        "name": student_info["name"],
        "class": student_info["class"],
        "source_images": [p.name for p in page_paths],
    }

    out_dir = OUTPUTS_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{final_id}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"    Saved to {out_path}")
    return {"student_id": final_id, "pages": len(page_paths), "text_len": len(combined_text)}


def parse_args():
    parser = argparse.ArgumentParser(description="Transcribe handwritten essays from images.")
    parser.add_argument("--folder", help="Folder name or index number (e.g. 'M2-5A BASELINE' or '2')")
    parser.add_argument("--pages", type=int, help="Number of images per essay (e.g. 2)")
    return parser.parse_args()


def resolve_folder(folders, folder_arg: str) -> Path | None:
    """Resolve --folder arg to a Path. Accepts index or name substring."""
    # Try numeric index
    try:
        idx = int(folder_arg) - 1
        if 0 <= idx < len(folders):
            return folders[idx]
    except ValueError:
        pass
    # Try case-insensitive name match
    folder_lower = folder_arg.lower()
    for f in folders:
        if f.name.lower() == folder_lower:
            return f
    # Try substring match
    for f in folders:
        if folder_lower in f.name.lower():
            return f
    return None


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    args = parse_args()
    folders = find_input_folders()
    if not folders:
        print(f"No subfolders found in {INPUTS_DIR}/")
        print(f"Create subdirectories there with your images (e.g. {INPUTS_DIR}/class_a/12345_1.jpg)")
        sys.exit(1)

    if args.folder:
        selected = resolve_folder(folders, args.folder)
        if not selected:
            print(f"Error: folder '{args.folder}' not found. Available folders:")
            for f in folders:
                print(f"  {f.name}")
            sys.exit(1)
    else:
        selected = show_menu(folders)

    pages_per_essay = args.pages or ask_page_count()

    print(f"\nProcessing folder: {selected.name}")
    print(f"Pages per essay: {pages_per_essay}")

    groups = group_images(selected, pages_per_essay)
    if not groups:
        print("No valid student image groups found.")
        sys.exit(1)

    print(f"Found {len(groups)} student(s) to process.\n")

    n_workers = min(MAX_WORKERS, len(groups))
    results = []
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        future_to_group = {
            executor.submit(process_student_group, group, selected.name): group
            for group in groups
        }
        for future in as_completed(future_to_group):
            group = future_to_group[future]
            try:
                r = future.result()
                if r:
                    results.append(r)
            except Exception as e:
                print(f"  Error processing student {group['student_id']}: {e}")

    print(f"\n{'='*50}")
    print(f"Done. Processed {len(results)}/{len(groups)} students.")
    print(f"Output: {OUTPUTS_DIR / selected.name}/")

    # Ghost report
    if GHOST_STUDENTS:
        print(f"\n{'!'*60}")
        print(f"  GHOST FILES DETECTED — {len(GHOST_STUDENTS)} student ID(s) not found in classlist")
        print(f"{'!'*60}")
        print("  These files have placeholder names. They will NOT be processed")
        print("  further (ERRANT, Supabase, PDF) until the IDs are fixed.")
        print()
        print(f"  {'Class':<17} {'Suspected ID':<14} {'Image':<32}")
        print(f"  {'-'*63}")
        for sid, info in sorted(GHOST_STUDENTS.items()):
            cls = info.get("class", "?")
            print(f"  {cls:<17} {sid:<14} {info['image']:<32}")

        # Write ghost report file
        ghost_report_path = OUTPUTS_DIR / selected.name / "GHOST_REPORT.txt"
        with open(ghost_report_path, "w", encoding="utf-8") as gr:
            gr.write(f"GHOST FILES REPORT — {date.today().isoformat()}\n")
            gr.write(f"Folder: {selected.name}\n")
            gr.write(f"{'='*60}\n\n")
            gr.write(f"{len(GHOST_STUDENTS)} student ID(s) not found in classlist:\n\n")
            for sid, info in sorted(GHOST_STUDENTS.items()):
                gr.write(f"  ID: {sid}\n")
                gr.write(f"  Image: {info['image']}\n")
                if "closest_match" in info:
                    m = info["closest_match"]
                    gr.write(f"  Closest match: {m['id']} ({m['name']}, dist={m['distance']})\n")
                if "text_name" in info:
                    gr.write(f"  Text suggests name: {info['text_name']}\n")
                gr.write(f"  JSON file: {sid}.json\n")
                gr.write("\n")
            gr.write("\nACTION REQUIRED:\n")
            gr.write("  1. Verify the student's actual ID\n")
            gr.write(f"  2. Update the JSON file in {OUTPUTS_DIR / selected.name}/ with the correct student_id\n")
            gr.write("  3. Delete this GHOST_REPORT.txt when all IDs are fixed\n")
        print(f"\n  Full report saved to: {ghost_report_path}")
        print("\n  ACTION REQUIRED:")
        print("    1. Verify each student's actual ID (check the image or classlist)")
        print("    2. Update the corresponding JSON file with the correct student_id")
        print("    3. Re-run ERRANT analysis after all IDs are fixed")
        print(f"{'!'*60}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
