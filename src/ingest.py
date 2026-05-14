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
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    sys.exit("Error: OPENROUTER_API_KEY not set. Add it to .env or export it.")

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
3. Use <br> to mark paragraph breaks. Use <br><br> for a blank line between paragraphs.
4. Do NOT introduce artificial line breaks within paragraphs. Preserve the natural flow of the writing.
5. Do NOT render crossed-out or deleted text. Skip it entirely.
6. If the writer used carats (^) or other insertion symbols, insert those words at their intended position so the natural flow of the passage is retained.

Return ONLY a valid JSON object with exactly these keys:
{"student_id": "5-digit number", "student_text": "the transcribed text with <br> for paragraph breaks"}

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
    pattern = re.compile(r"^(\d+)_(\d+)")
    images = []
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            m = pattern.match(f.stem)
            if m:
                student_id = m.group(1)
                page_num = int(m.group(2))
                images.append((student_id, page_num, f))
            else:
                print(f"  Warning: skipped file with unexpected name: {f.name}")

    groups = {}
    for student_id, page_num, path in images:
        groups.setdefault(student_id, []).append((page_num, path))
    for sid in groups:
        groups[sid].sort(key=lambda x: x[0])

    result = []
    for student_id, pages in groups.items():
        if len(pages) < pages_per_essay:
            print(f"  Warning: student {student_id} has {len(pages)} pages, expected {pages_per_essay}. Processing with what exists.")
        result.append({"student_id": student_id, "pages": [p[1] for p in pages]})
    result.sort(key=lambda x: x["student_id"])
    return result


def preprocess_image(image_path):
    img = Image.open(image_path)
    img = img.convert("L")
    img.thumbnail((MAX_LONG_SIDE, MAX_LONG_SIDE), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def call_openrouter(data_url):
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

    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Try to parse JSON from the response
            parsed = try_parse_json(content)
            if parsed:
                return parsed

            print(f"  Warning: could not parse model response as JSON. Raw: {content[:200]}")
            return None

        except requests.exceptions.HTTPError as e:
            status = r.status_code
            if status in (429, 502, 503) and attempt < MAX_RETRIES:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"  Rate limit/server error ({status}), retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            print(f"  Error: HTTP {status} — {e}")
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < MAX_RETRIES:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"  Connection error, retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            print(f"  Error: {e}")
            return None
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

        if idx == 1:
            extracted_id = sid if len(sid) == 5 else None
            if not extracted_id:
                print(f"    Warning: could not extract valid 5-digit student ID from page 1 (got '{sid}')")

        if text:
            page_texts.append(text)
        else:
            print(f"    Warning: page {idx} returned empty text")

        # Track token usage if available (OpenRouter returns usage info)
        # Note: not strictly necessary for functionality but useful for logging

        jitter()

    if not page_texts:
        print(f"  No text transcribed for {student_id}, skipping.")
        return None

    combined_text = "<br>".join(page_texts)
    final_id = extracted_id or student_id

    output = {"student_id": final_id, "student_text": combined_text}

    out_dir = OUTPUTS_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{student_id}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"    Saved to {out_path}")
    return {"student_id": final_id, "pages": len(page_paths), "text_len": len(combined_text)}


def main():
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

    results = []
    for group in groups:
        r = process_student_group(group, selected.name)
        if r:
            results.append(r)

    print(f"\n{'='*50}")
    print(f"Done. Processed {len(results)}/{len(groups)} students.")
    print(f"Output: {OUTPUTS_DIR / selected.name}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
