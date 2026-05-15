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
from rapidfuzz.distance import Levenshtein

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

CORRECTION_MODEL = "mistralai/mistral-small-3.2-24b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

OUTPUTS_DIR = Path("outputs")
LOCAL_WORKING_DIR = Path("local-working")

TEMPERATURE = 0.1
DOUBLE_CHECK_TEMP = 0.3
MODEL_CONTEXT_LIMIT = 32000
MAX_RETRIES = 3
REQUEST_TIMEOUT = 45
JITTER_MIN = 0.5
JITTER_MAX = 1.5
MULTI_TOKEN_THRESHOLD = 3


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


def call_model(text, temperature=TEMPERATURE):
    if not API_KEY:
        print("  Error: OPENROUTER_API_KEY not set")
        return None

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
        "temperature": temperature,
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

    aux_verbs = {
        "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't", "shouldn't",
        "can't", "cannot", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
        "hadn't", "does", "do", "did", "is", "are", "am", "was", "were", "have", "has", "had",
    }
    if o_lower in aux_verbs and c_lower in aux_verbs:
        return "R:VERB:TENSE"

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
    return re.sub(r"</u>(?!\s|$|<)", "</u> ", marked_up)


def intersect_edits(edits_a, edits_b):
    matched_b = set()
    confirmed = []
    for ea in edits_a:
        for i, eb in enumerate(edits_b):
            if i in matched_b:
                continue
            if ea.o_start == eb.o_start and ea.o_end == eb.o_end and ea.type == eb.type:
                confirmed.append(ea)
                matched_b.add(i)
                break
    return confirmed


def _make_edit(o_start, o_end, o_toks, o_str, c_start, c_end, c_toks, c_str, etype):
    return type("Edit", (), {
        "o_start": o_start, "o_end": o_end,
        "o_toks": o_toks, "o_str": o_str,
        "c_start": c_start, "c_end": c_end,
        "c_toks": c_toks, "c_str": c_str,
        "type": etype,
    })


def pre_split_edits(annotator, edits, orig_doc, cor_doc):
    other_edits = [e for e in edits if e.type == "R:OTHER" and e.o_toks and e.c_toks]
    if not other_edits:
        return edits

    alignment = annotator.align(orig_doc, cor_doc)
    split_edits = annotator.merge(alignment, merging="all-split")
    for e in split_edits:
        e = annotator.classify(e)

    result = []
    for e in edits:
        if e.type == "R:OTHER" and e.o_toks and e.c_toks:
            decomposed = [se for se in split_edits if se.o_start >= e.o_start and se.o_end <= e.o_end]
            if decomposed and any(de.type not in ("OTHER", "UNK") for de in decomposed):
                for de in decomposed:
                    de_type = de.type
                    if de_type in ("OTHER", "R:OTHER") and de.o_toks and de.c_toks:
                        de_type = post_classify_other(de.o_str, de.c_str)
                    result.append(_make_edit(
                        de.o_start, de.o_end, de.o_toks, de.o_str,
                        de.c_start, de.c_end, de.c_toks, de.c_str,
                        de_type,
                    ))
            else:
                result.append(e)
        else:
            result.append(e)

    return result


def build_metadata(edits, corrected_text, original_text):
    total = len(edits)
    oc_count = 0
    oc_warnings = []
    spans = []
    multi_tok = 0

    for e in edits:
        span = e.o_end - e.o_start
        spans.append(span)
        if span > MULTI_TOKEN_THRESHOLD and e.o_toks and e.c_toks:
            oc_count += 1
            oc_warnings.append({
                "span": span,
                "original": str(e.o_str).strip(),
                "corrected": str(e.c_str).strip(),
            })
        if span > 1:
            multi_tok += 1

    max_span = max(spans) if spans else 0
    avg_span = round(sum(spans) / len(spans), 2) if spans else 0

    identity = original_text.strip() == corrected_text.strip()

    return {
        "model": CORRECTION_MODEL,
        "temperature": TEMPERATURE,
        "identity_check": identity,
        "overcorrection_count": oc_count,
        "overcorrection_warnings": oc_warnings,
        "total_edit_count": total,
        "edit_width_stats": {
            "max_span": max_span,
            "avg_span": avg_span,
            "multi_token_edits": multi_tok,
        },
    }


def classify_edits(edits):
    error_groups = {}
    uncategorised = []

    for e in edits:
        e_type = e.type
        if e_type in ("OTHER", "R:OTHER") and e.o_toks and e.c_toks:
            e_type = post_classify_other(e.o_str, e.c_str)
        if e_type == "OTHER" or e_type == "UNK":
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
    return errors_list, uncategorised


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

    annotator = errant.load("en")

    # Double-check: run correction at two different temperatures
    print("  Correcting text (pass 1, temp=0.1)...")
    corrected_a = call_model(original_text, TEMPERATURE)
    if corrected_a:
        time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))

    print("  Correcting text (pass 2, temp=0.3)...")
    corrected_b = call_model(original_text, DOUBLE_CHECK_TEMP)

    # Use the conservative (lower temp) version as primary
    corrected_text = corrected_a or corrected_b or original_text
    if not corrected_a and not corrected_b:
        print("  Both correction passes failed, using original as-is.")
        corrected_text = original_text

    corrected_text = corrected_text.strip()
    print(f"  Corrected length: {len(corrected_text)} chars")

    # GAP-2: Noop check — if text is identical, skip ERRANT
    if original_text.strip() == corrected_text.strip():
        print("  No corrections needed — text unchanged by model.")
        metadata = build_metadata([], corrected_text, original_text)
        output = {
            "student_id": student_id,
            "original_text": original_text,
            "corrected_text": corrected_text,
            "sentence_pairs": [],
            "errant_analysis": {"errors": [], "uncategorised": []},
            "corrected_with_markup": original_text,
            "error_rate": 0,
            "metadata": metadata,
        }
        return write_output(output, file_path)

    both_succeeded = corrected_a is not None and corrected_b is not None

    cor_doc_a = annotator.parse(corrected_a) if corrected_a else orig_doc
    edits_a = annotator.annotate(orig_doc, cor_doc_a)

    cor_doc_b = annotator.parse(corrected_b) if corrected_b else orig_doc
    edits_b = annotator.annotate(orig_doc, cor_doc_b) if corrected_b else []

    # GAP-3: Intersect edits from both passes
    confirmed_edits = intersect_edits(edits_a, edits_b)
    uncertain_count = max(len(edits_a), len(edits_b)) - len(confirmed_edits) if both_succeeded else 0
    use_edits = confirmed_edits if confirmed_edits else (edits_b if corrected_a is None else edits_a)

    cor_doc = annotator.parse(corrected_text)

    # GAP-4: Pre-split multi-token edits
    use_edits = pre_split_edits(annotator, use_edits, orig_doc, cor_doc)

    # GAP-1: Overcorrection detection + GAP-5: Metadata — built during classification
    errors_list, uncategorised = classify_edits(use_edits)
    metadata = build_metadata(use_edits, corrected_text, original_text)
    metadata["uncertain_edit_count"] = uncertain_count if both_succeeded else len(use_edits) // 2

    marked_up = fix_markup_spacing(generate_markup(orig_doc, use_edits))

    cor_sentences = [sent.text.strip() for sent in cor_doc.sents]
    max_pairs = min(len(orig_sentences), len(cor_sentences)) if orig_sentences else 0
    sentence_pairs = []
    for i in range(max_pairs):
        sentence_pairs.append({"original": orig_sentences[i], "corrected": cor_sentences[i]})

    word_count = len(orig_doc)
    correction_count = sum(eg["count"] for eg in errors_list)
    error_rate = round((correction_count / word_count * 100)) if word_count > 0 else 0

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
        "metadata": metadata,
    }

    return write_output(output, file_path)


def write_output(output, file_path):
    folder_name = file_path.parent.name
    student_id = output.get("student_id", "unknown")
    output_filename = f"{folder_name}-{student_id}.json"
    output_path = LOCAL_WORKING_DIR / output_filename

    LOCAL_WORKING_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Saved to: {output_path}")
    print(f"  Errors: {output['errant_analysis']['errors']}")
    tc = sum(e["count"] for e in output["errant_analysis"]["errors"])
    print(f"  Total corrections: {tc}, rate: {output['error_rate']}%")
    print(f"  Uncat: {len(output['errant_analysis']['uncategorised'])}")
    if output["metadata"]["identity_check"]:
        print("  Note: text required no corrections")
    if output["metadata"]["overcorrection_count"] > 0:
        print(f"  Warning: {output['metadata']['overcorrection_count']} potential overcorrection(s) detected")

    return output


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

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
