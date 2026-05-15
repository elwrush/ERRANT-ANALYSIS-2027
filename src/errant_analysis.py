#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
import requests
import spacy
import errant

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    sys.exit("Error: OPENROUTER_API_KEY not set. Add it to .env or export it.")

CORRECTION_MODEL = "mistralai/mistral-small-3.2-24b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

OUTPUTS_DIR = Path("outputs")
LOCAL_WORKING_DIR = Path("local-working")

TEMPERATURE = 0.1
MODEL_CONTEXT_LIMIT = 32000
MAX_RETRIES = 3
REQUEST_TIMEOUT = 45
JITTER_MIN = 0.5
JITTER_MAX = 1.5



CORRECTION_PROMPT = """You are a grammar correction tool. Correct the following student essay.

Rules:
- Correct ONLY grammatical errors (verb form, subject-verb agreement, articles, prepositions, spelling).
- Make the MINIMAL change needed — change only the error, leave everything else untouched.
- Do NOT rephrase, improve style, change vocabulary, or alter meaning.
- Do NOT add markdown, bold, asterisks, quotes, or any formatting.
- Do NOT add any commentary, explanation, or notes.
- Preserve the original paragraph breaks and sentence structure.
- Return ONLY the corrected plain text, nothing else.

Original text:
{text}

Corrected text:"""


def find_output_files():
    if not OUTPUTS_DIR.exists():
        return []
    files = []
    for d in sorted(OUTPUTS_DIR.iterdir()):
        if d.is_dir():
            for f in sorted(d.iterdir()):
                if f.suffix == ".json":
                    files.append(f)
    return files


def show_menu(files):
    print("\nAvailable output files:")
    for i, f in enumerate(files, 1):
        rel = f.relative_to(OUTPUTS_DIR)
        print(f"  {i}. {rel}")
    while True:
        try:
            choice = input(f"\nSelect file (1-{len(files)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
        except ValueError:
            pass
        print(f"Invalid choice. Enter a number 1-{len(files)}.")


def call_model(text):
    est_tokens = len(text) // 4
    if est_tokens > MODEL_CONTEXT_LIMIT:
        print(f"  Error: text too long (~{est_tokens} tokens, limit {MODEL_CONTEXT_LIMIT})")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": CORRECTION_MODEL,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": CORRECTION_PROMPT.format(text=text)},
        ],
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"].strip()
            if content:
                return content
            raise ValueError("Empty response")
        except Exception as e:
            if attempt < MAX_RETRIES:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"  API error, retrying in {delay:.1f}s... ({e})")
                time.sleep(delay)
            else:
                print(f"  Failed after {MAX_RETRIES} retries: {e}")
                return None


def post_classify_other(o_str, c_str):
    if not o_str or not c_str:
        if not o_str and c_str.strip().lower() in {"the", "a", "an", "some", "any", "this", "that", "these", "those"}:
            return "M:DET"
        return "OTHER"

    o_lower = o_str.lower().strip()
    c_lower = c_str.lower().strip()

    if o_lower == c_lower:
        return "R:ORTH"
    if re.sub(r"\W", "", o_lower) == re.sub(r"\W", "", c_lower):
        return "R:ORTH"

    # Contraction/auxiliary changes → verb tense (before spelling)
    aux_verbs = {
        "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't", "shouldn't",
        "can't", "cannot", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
        "hadn't", "does", "do", "did", "is", "are", "am", "was", "were", "have", "has", "had",
    }
    if o_lower in aux_verbs and c_lower in aux_verbs:
        return "R:VERB:TENSE"

    from rapidfuzz.distance import Levenshtein
    sim = Levenshtein.normalized_similarity(o_lower, c_lower)
    if sim > 0.55:
        return "R:SPELL"

    if o_lower[:3] == c_lower[:3] and len(o_str) > 3:
        return "R:MORPH"

    articles = {"the", "a", "an", "some", "any", "this", "that", "these", "those"}
    if o_lower in articles or c_lower in articles:
        return "R:DET"

    preps = {"in", "on", "at", "to", "for", "with", "by", "from", "of", "about", "into", "through", "during"}
    if o_lower in preps or c_lower in preps:
        return "R:PREP"

    # Contraction/auxiliary changes → verb tense
    aux_verbs = {
        "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't", "shouldn't",
        "can't", "cannot", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
        "hadn't", "does", "do", "did", "is", "are", "am", "was", "were", "have", "has", "had",
    }
    if o_lower in aux_verbs and c_lower in aux_verbs:
        return "R:VERB:TENSE"

    return "OTHER"


def generate_markup(orig_doc, edits):
    edits = sorted(edits, key=lambda e: e.o_start)
    tokens = list(orig_doc)
    result_parts = []
    edit_idx = 0
    i = 0

    while i < len(tokens):
        if edit_idx < len(edits) and i == edits[edit_idx].o_start:
            edit = edits[edit_idx]
            if edit.o_str.rstrip() == edit.c_str.rstrip():
                result_parts.append(tokens[i].text_with_ws if i < len(tokens) else "")
                i += 1
                edit_idx += 1
                continue
            if not edit.o_toks and not edit.c_toks:
                edit_idx += 1
                continue
            if edit.c_toks:
                result_parts.append(f"<u>{edit.c_str}</u>")
            i = edit.o_end if edit.o_toks else (edit.o_end if edit.o_end > edit.o_start else i)
            edit_idx += 1
        else:
            result_parts.append(tokens[i].text_with_ws)
            i += 1

    return "".join(result_parts)


def fix_markup_spacing(marked_up):
    """Add space after </u> when directly followed by text (no space consumed)."""
    return re.sub(r"</u>(?!\s|$|<)", "</u> ", marked_up)


def process_file(file_path):
    print(f"\n=== Processing: {file_path.relative_to(OUTPUTS_DIR)} ===")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    student_id = data.get("student_id", "unknown")
    original_text = data.get("student_text", "").strip()

    if not original_text:
        print("  Empty student_text, skipping.")
        return None

    print(f"  Student: {student_id}")
    print(f"  Original length: {len(original_text)} chars")
    print(f"  Model: {CORRECTION_MODEL}")

    nlp = spacy.load("en_core_web_sm")
    orig_doc = nlp(original_text)
    orig_sentences = [sent.text.strip() for sent in orig_doc.sents]

    print("  Correcting text...")
    corrected_text = call_model(original_text)
    if corrected_text:
        time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
    if not corrected_text:
        print("  Correction failed, using original as-is.")
        corrected_text = original_text

    corrected_text = corrected_text.strip()
    print(f"  Corrected length: {len(corrected_text)} chars")

    annotator = errant.load("en")
    cor_doc = annotator.parse(corrected_text)
    edits = annotator.annotate(orig_doc, cor_doc)

    error_groups = {}
    uncategorised = []

    for e in edits:
        e_type = e.type
        if e_type in ("OTHER", "R:OTHER") and e.o_toks and e.c_toks:
            e_type = post_classify_other(e.o_str, e.c_str)
        if e_type == "OTHER" or e_type == "UNK":
            # Skip same-text entries (tokenization artifacts)
            if e.o_str.rstrip() == e.c_str.rstrip() and e.o_str.strip():
                continue
            uncategorised.append({
                "orig": str(e.o_str),
                "cor": str(e.c_str),
                "orig_start": e.o_start,
                "orig_end": e.o_end,
            })
        if e_type in ("UNK", "U:SPACE"):
            continue
        example = f"{e.o_str.strip()} \u2192 {e.c_str.strip()}" if e.o_str and e.c_str else str(e.c_str)
        if e_type not in error_groups:
            error_groups[e_type] = {"type": e_type, "example": example, "count": 0}
        error_groups[e_type]["count"] += 1

    errors_list = sorted(error_groups.values(), key=lambda x: x["count"], reverse=True)
    marked_up = fix_markup_spacing(generate_markup(orig_doc, edits))

    cor_sentences = [sent.text.strip() for sent in list(cor_doc.sents)]
    max_pairs = min(len(orig_sentences), len(cor_sentences)) if orig_sentences else 0
    sentence_pairs = []
    for i in range(max_pairs):
        sentence_pairs.append({"original": orig_sentences[i], "corrected": cor_sentences[i]})

    word_count = len(list(orig_doc))
    correction_count = sum(eg["count"] for eg in errors_list)
    error_rate = round((correction_count / word_count * 100)) if word_count > 0 else 0

    folder_name = file_path.parent.name
    output_filename = f"{folder_name}-{student_id}.json"
    output_path = LOCAL_WORKING_DIR / output_filename

    output = {
        "student_id": student_id,
        "original_text": original_text,
        "corrected_text": corrected_text,
        "sentence_pairs": sentence_pairs,
        "errant_analysis": {
            "errors": errors_list,
            "uncategorised": uncategorised,
        },
        "corrected_with_markup": marked_up,
        "error_rate": error_rate,
    }

    LOCAL_WORKING_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Saved to: {output_path}")
    print(f"  Errors: {correction_count} total, rate: {error_rate}%")
    print(f"  Uncat: {len(uncategorised)}")

    return output


def main():
    files = find_output_files()
    if not files:
        print(f"No JSON files found in {OUTPUTS_DIR}/")
        print("Run ingest-images first to produce output files.")
        sys.exit(1)

    selected = show_menu(files)
    result = process_file(selected)

    if result:
        print(f"\n{'='*50}")
        print(f"Complete. Output in {LOCAL_WORKING_DIR}/")
        tc = sum(e["count"] for e in result["errant_analysis"]["errors"])
        print(f"Errors detected: {tc}")
        print(f"Error rate: {result['error_rate']}%")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
