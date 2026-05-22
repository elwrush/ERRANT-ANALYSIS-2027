#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import random
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from _retry import RetryableError, retry

MAX_WORKERS = 5

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

MODEL = "google/gemini-2.5-flash-lite-preview-09-2025"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

INPUTS_DIR = Path("inputs")
OUTPUTS_DIR = Path("outputs")

MAX_LONG_SIDE = 1024
JPEG_QUALITY = 90
JITTER_MIN = 0.5
JITTER_MAX = 2.0
MAX_RETRIES = 5
REQUEST_TIMEOUT = 30


SYSTEM_PROMPT = """You are a handwriting transcription tool. Your task is to transcribe handwritten English essays EXACTLY as written — preserve ALL spelling, grammar, and vocabulary errors. You are a transcriber, NOT a proofreader. Do not correct anything.

Rules:
1. Extract the 5-digit student ID from the ID field on the page.
2. Transcribe the essay text verbatim.
3. CRITICAL: Insert \\n ONLY at paragraph boundaries. NEVER insert \\n at handwritten line endings. A handwritten line ending is just a page-width wrap, not a paragraph break. The entire page should be transcribed as a single flowing block with \\n only where the writer intended a new paragraph (indentation, blank line, topic change). A letter's salutation ("Dear X,") and closing ("Sincerely," / "See you soon!") are distinct paragraphs; separate them with \\n.
4. NEVER wrap lines at a fixed character width. Each paragraph reads as one continuous line with no \\n except at paragraph boundaries. If the output has a \\n at every handwritten line, you are doing it WRONG.
5. Do NOT render crossed-out or deleted text. Skip it entirely.
6. Do NOT render any drawings, illustrations, doodles, emoji, or decorations (e.g. smiley faces, hearts, stars, apples, flowers). Skip them entirely. They are not part of the written text.
7. If the writer used carats (^) or other insertion symbols, insert those words at their intended position so the natural flow of the passage is retained.

Return ONLY a valid JSON object with exactly these keys:
{"student_id": "5-digit number", "student_text": "the transcribed text with \\n ONLY at paragraph boundaries"}

REMEMBER: \\n must ONLY appear at paragraph boundaries (indentation, blank line, topic change). Never at handwritten line wraps. Every handwritten line ending should flow into the next word without \\n.

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

        sid = result.get("student_id", "").strip()
        text = result.get("student_text", "").strip()
        # Squash any newlines the model inserted at line-wrap positions
        text = " ".join(text.split())

        if idx == 1:
            extracted_id = sid if len(sid) == 5 else None
            if not extracted_id:
                print(f"    Warning: could not extract valid 5-digit student ID from page 1 (got '{sid}')")

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

    output = {
        "student_id": final_id,
        "student_text": combined_text,
        "source_images": [p.name for p in page_paths],
    }

    out_dir = OUTPUTS_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{final_id}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"    Saved to {out_path}")
    return {"student_id": final_id, "pages": len(page_paths), "text_len": len(combined_text)}


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    folders = find_input_folders()
    if not folders:
        print(f"No subfolders found in {INPUTS_DIR}/")
        print(f"Create subdirectories there with your images (e.g. {INPUTS_DIR}/class_a/12345_1.jpg)")
        sys.exit(1)

    selected = show_menu(folders)
    pages_per_essay = ask_page_count()

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
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
