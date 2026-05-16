#!/usr/bin/env python3
import os
import re
import sys
import json
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from _retry import RetryableError, retry
from generate_report import esc
import requests
import spacy
import errant
from rapidfuzz.distance import Levenshtein

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

CORRECTION_MODEL = "google/gemma-4-31b-it"
SUMMARY_MODEL = "google/gemma-4-31b-it"
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
SUMMARY_TEMPERATURE = 0.8
MAX_WORKERS = 5

STUDENTS_PATH = Path("docs/students.txt")


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
    est_tokens = len(text) // 4
    if est_tokens > MODEL_CONTEXT_LIMIT:
        print(f"  Error: text too long (~{est_tokens} tokens, limit {MODEL_CONTEXT_LIMIT})")
        return None
    return _call_api(CORRECTION_PROMPT.format(text=text), temperature)


def call_model_custom(prompt_content, temperature=TEMPERATURE, model=None):
    return _call_api(prompt_content, temperature, model=model)


@retry(max_retries=MAX_RETRIES)
def _call_api(content, temperature, model=None):
    if not API_KEY:
        print("  Error: OPENROUTER_API_KEY not set")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model if model else CORRECTION_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": content},
        ],
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"].strip()
        if content:
            return content
        raise ValueError("Empty response")
    except Exception as e:
        raise RetryableError(str(e))


ERRANT_CODE_NAMES = {
    # Noun errors
    "R:NOUN": "Problems with nouns",
    "R:NOUN:NUM": "Problems with singular and plural nouns",
    "R:NOUN:POSS": "Problems with possessive nouns",
    "R:NOUN:INFL": "Problems with noun inflection",
    # Verb errors
    "R:VERB": "Problems with verbs",
    "R:VERB:TENSE": "Problems with verb tense",
    "R:VERB:SVA": "Problems with subject-verb agreement",
    "R:VERB:FORM": "Problems with verb form (gerunds and infinitives)",
    "R:VERB:INFL": "Problems with verb inflection",
    # Adjective errors
    "R:ADJ": "Problems with adjectives",
    "R:ADJ:FORM": "Problems with adjective form (comparatives and superlatives)",
    # Other POS errors
    "R:ADV": "Problems with adverbs",
    "R:PREP": "Problems with prepositions",
    "R:PRON": "Problems with pronouns",
    "R:DET": "Problems with determiners (articles: a, an, the)",
    "R:CONJ": "Problems with conjunctions",
    "R:PART": "Problems with particles",
    "R:PUNCT": "Problems with punctuation",
    # Spelling and orthography
    "R:SPELL": "Spelling or capitalisation mistakes",
    "R:ORTH": "Capitalisation and spacing errors",
    "R:MORPH": "Problems with word formation (prefixes and suffixes)",
    # Structure
    "R:WO": "Problems with word order",
    "R:CONTR": "Problems with contractions",
    # Missing / Unnecessary error codes
    "M:NOUN": "Missing noun",
    "M:NOUN:NUM": "Missing plural noun ending",
    "M:VERB": "Missing verb",
    "M:VERB:TENSE": "Missing auxiliary verb",
    "M:VERB:FORM": "Missing verb form",
    "M:PREP": "Missing preposition",
    "M:PRON": "Missing pronoun",
    "M:DET": "Missing determiner (a, an, the)",
    "M:CONJ": "Missing conjunction",
    "M:PART": "Missing particle",
    "M:PUNCT": "Missing punctuation",
    "U:NOUN": "Unnecessary noun",
    "U:VERB": "Unnecessary verb",
    "U:PREP": "Unnecessary preposition",
    "U:PRON": "Unnecessary pronoun",
    "U:DET": "Unnecessary determiner",
    "U:CONJ": "Unnecessary conjunction",
    "U:PART": "Unnecessary particle",
    "U:PUNCT": "Unnecessary punctuation",
    # Generic fallback
    "OTHER": "Other errors",
    "UNK": "Unidentified error type",
}


ERRANT_CODE_TO_COLUMN = {
    "R:NOUN": "r_noun", "R:NOUN:NUM": "r_noun_num", "R:NOUN:POSS": "r_noun_poss", "R:NOUN:INFL": "r_noun_infl",
    "R:VERB": "r_verb", "R:VERB:TENSE": "r_verb_tense", "R:VERB:SVA": "r_verb_sva",
    "R:VERB:FORM": "r_verb_form", "R:VERB:INFL": "r_verb_infl",
    "R:ADJ": "r_adj", "R:ADJ:FORM": "r_adj_form",
    "R:ADV": "r_adv", "R:PREP": "r_prep", "R:PRON": "r_pron", "R:DET": "r_det",
    "R:CONJ": "r_conj", "R:PART": "r_part", "R:PUNCT": "r_punct",
    "R:SPELL": "r_spell", "R:ORTH": "r_orth", "R:MORPH": "r_morph",
    "R:WO": "r_wo", "R:CONTR": "r_contr",
    "M:NOUN": "m_noun", "M:NOUN:NUM": "m_noun_num",
    "M:VERB": "m_verb", "M:VERB:TENSE": "m_verb_tense", "M:VERB:FORM": "m_verb_form",
    "M:PREP": "m_prep", "M:PRON": "m_pron", "M:DET": "m_det",
    "M:CONJ": "m_conj", "M:PART": "m_part", "M:PUNCT": "m_punct",
    "U:NOUN": "u_noun", "U:VERB": "u_verb", "U:PREP": "u_prep", "U:PRON": "u_pron",
    "U:DET": "u_det", "U:CONJ": "u_conj", "U:PART": "u_part", "U:PUNCT": "u_punct",
    "OTHER": "other", "UNK": "unk",
}

ERROR_CODE_COLUMNS = list(ERRANT_CODE_TO_COLUMN.values())


def human_error_type(err_type):
    """Convert an ERRANT error code to a human-readable description."""
    if err_type in ERRANT_CODE_NAMES:
        return ERRANT_CODE_NAMES[err_type]
    prefix = err_type[:2] if err_type[1] == ":" else ""
    body = err_type[2:] if prefix else err_type
    if body in ERRANT_CODE_NAMES:
        desc = ERRANT_CODE_NAMES[body]
        if prefix == "M:":
            return f"Missing: {desc.lower()}"
        if prefix == "U:":
            return f"Unnecessary: {desc.lower()}"
        return desc
    return err_type


SUMMARY_PROMPT = """Write a feedback paragraph in this exact format for {name}, a Thai ESL student (error rate: {error_rate}%):

[One sentence of specific, genuine praise about their writing — mention something concrete they did well, like a word they used effectively or an idea they expressed clearly]

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. *[Human-readable error description (ERROR_CODE):* [simple explanation of what they did wrong]. For example, you wrote "[brief quote with error]". It is better to write "[corrected version]".
2. *[Human-readable error description (ERROR_CODE):* [simple explanation]. For example, you wrote "[brief quote with error]". It is better to write "[corrected version]".
3. *[Human-readable error description (ERROR_CODE):* [simple explanation]. For example, you wrote "[brief quote with error]". It is better to write "[corrected version]".

Use ONLY errors from this list:
{error_list}

Format error types as: Human-readable description (CODE) — e.g. "Problems with singular and plural nouns (R:NOUN:NUM)"

The student wrote this:
{original_text}

Output ONLY the feedback paragraph above. Nothing before or after."""


def lookup_student_info(student_id: str) -> dict:
    if not STUDENTS_PATH.exists():
        return {}
    with open(STUDENTS_PATH, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)
        for cols in reader:
            if len(cols) >= 3 and cols[1].strip() == student_id:
                return {"class": cols[0].strip(), "name": cols[2].strip()}
    return {}


def _sanitize_unicode(text):
    """Replace problematic Unicode characters that break Typst rendering."""
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--",
        "\u2026": "...",
        "\u00a0": " ",
        "\ufffd": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def generate_summary(output: dict) -> str | None:
    errors = output.get("errant_analysis", {}).get("errors", [])
    if not errors:
        return "Your writing was very accurate — no corrections were needed. Keep up the great work!"
    top5 = errors[:5]
    error_list = "\n".join(
        f"- {human_error_type(e['type'])} ({e['type']}): {e['count']} time(s) (e.g. {e['example']})"
        for e in top5
    )
    name = output.get("name", "student")
    # Use full student text for accurate quoting
    sample = output.get("original_text", "")[:2000]
    prompt = SUMMARY_PROMPT.format(
        name=name,
        error_rate=output["error_rate"],
        error_list=error_list,
        original_text=sample,
    )
    result = call_model_custom(prompt, SUMMARY_TEMPERATURE, model=SUMMARY_MODEL)
    if result:
        result = _sanitize_unicode(result)
    return result if result else f"Your writing had {output['error_rate']}% errors. Keep practicing!"


def insert_error_reports(output: dict):
    try:
        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ESL_KEY")
        if not supabase_url or not supabase_key:
            print("  Supabase credentials not set — skipping error_reports insert")
            return
        client = create_client(supabase_url, supabase_key)
        row = {
            "student_id": output["student_id"],
            "class": output.get("class", ""),
            "name": output.get("name", ""),
            "error_percent": output["error_rate"],
            "summary": output.get("summary", ""),
        }
        for col in ERROR_CODE_COLUMNS:
            row[col] = 0
        errors = output.get("errant_analysis", {}).get("errors", [])
        for e in errors:
            col = ERRANT_CODE_TO_COLUMN.get(e["type"])
            if col:
                row[col] = e["count"]
        client.table("error_reports").insert(row).execute()
        print(f"  Inserted into error_reports for {output['student_id']} ({len(errors)} error types)")
    except Exception as e:
        print(f"  Warning: could not insert into error_reports: {e}")


def post_classify_other(o_str, c_str):
    if not o_str or not c_str:
        if not o_str and c_str.strip().lower() in {"the", "a", "an", "some", "any", "this", "that", "these", "those"}:
            return "M:DET"
        return "OTHER"

    o_lower = o_str.lower().strip()
    c_lower = c_str.lower().strip()

    aux_verbs = {
        "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't", "shouldn't",
        "can't", "cannot", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
        "hadn't", "does", "do", "did", "is", "are", "am", "was", "were", "have", "has", "had",
    }
    if o_lower in aux_verbs and c_lower in aux_verbs:
        return "R:VERB:TENSE"

    sim = Levenshtein.normalized_similarity(o_lower, c_lower)
    if sim > 0.55:
        if o_lower == c_lower:
            return "R:ORTH"
        return "R:SPELL"

    if o_lower == c_lower:
        return "R:ORTH"
    if re.sub(r"\W", "", o_lower) == re.sub(r"\W", "", c_lower):
        return "R:ORTH"

    if o_lower[:3] == c_lower[:3] and len(o_str) > 3:
        return "R:MORPH"

    articles = {"the", "a", "an", "some", "any", "this", "that", "these", "those"}
    if o_lower in articles or c_lower in articles:
        return "R:DET"

    preps = {"in", "on", "at", "to", "for", "with", "by", "from", "of", "about", "into", "through", "during"}
    if o_lower in preps or c_lower in preps:
        return "R:PREP"

    return "OTHER"


def build_corrected_typst(orig_doc, edits):
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
                result_parts.append(f"#underline[{esc(edit.c_str)}]")
                # Preserve trailing whitespace from last consumed token
                if edit.o_toks:
                    last_idx = edit.o_end - 1
                    if 0 <= last_idx < len(tokens):
                        orig_tok = tokens[last_idx]
                        ws = orig_tok.text_with_ws[len(orig_tok.text):]
                        result_parts.append(ws)
            i = edit.o_end if edit.o_toks else (edit.o_end if edit.o_end > edit.o_start else i)
            edit_idx += 1
            # Preserve whitespace between consecutive edits
            if edit_idx < len(edits) and i < len(tokens) and i == edits[edit_idx].o_start:
                if tokens[i].text_with_ws and not tokens[i].text_with_ws[0].isspace():
                    pass  # next edit starts on a non-whitespace token, no extra space needed
                elif i < len(tokens) and not result_parts[-1].endswith(" "):
                    result_parts.append(" ")
        else:
            result_parts.append(tokens[i].text_with_ws)
            i += 1

    result = "".join(result_parts)
    result = re.sub(r"\](?=[^\s\]\)])", "] ", result)
    return result


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
        example = f"{e.o_str.strip()} -> {e.c_str.strip()}" if e.o_str and e.c_str else str(e.c_str)
        if e_type not in error_groups:
            error_groups[e_type] = {"type": e_type, "example": example, "count": 0}
        error_groups[e_type]["count"] += 1

    errors_list = sorted(error_groups.values(), key=lambda x: x["count"], reverse=True)
    return errors_list, uncategorised


def process_file(file_path, nlp=None, annotator=None):
    print(f"\n=== Processing: {file_path.relative_to(OUTPUTS_DIR)} ===")
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    student_id = data.get("student_id", "unknown")
    original_text = data.get("student_text", "").strip()
    word_count = data.get("word_count", 0)

    if not original_text:
        print("  Empty student_text, skipping.")
        return None

    student_info = lookup_student_info(student_id)
    print(f"  Student: {student_id}")
    print(f"  Student info: {student_info}")

    if nlp is None:
        nlp = spacy.load("en_core_web_sm")
    orig_doc = nlp(original_text)
    orig_sentences = [sent.text.strip() for sent in orig_doc.sents]

    if annotator is None:
        annotator = errant.load("en")

    # Double-check: run correction at two different temperatures in parallel
    print("  Correcting text (pass 1, temp=0.1) and (pass 2, temp=0.3)...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(call_model, original_text, TEMPERATURE)
        future_b = executor.submit(call_model, original_text, DOUBLE_CHECK_TEMP)
        corrected_a = future_a.result()
        corrected_b = future_b.result()

    # Use the conservative (lower temp) version as primary
    corrected_text = corrected_a or corrected_b or original_text
    if not corrected_a and not corrected_b:
        print("  Both correction passes failed, using original as-is.")
        corrected_text = original_text

    corrected_text = corrected_text.strip()
    print(f"  Corrected length: {len(corrected_text)} chars")

    output = _build_output(student_id, original_text, corrected_text, word_count, student_info, [],
                           {"errors": [], "uncategorised": []}, original_text, 0, [])

    # Noop check — if text is identical, skip ERRANT
    if original_text.strip() == corrected_text.strip():
        print("  No corrections needed — text unchanged by model.")
        output["metadata"] = build_metadata([], corrected_text, original_text)
        return _finalize_output(output, file_path)

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

    # GAP-1: Overcorrection detection + GAP-5: Metadata
    errors_list, uncategorised = classify_edits(use_edits)
    metadata = build_metadata(use_edits, corrected_text, original_text)
    metadata["uncertain_edit_count"] = uncertain_count if both_succeeded else len(use_edits) // 2

    corrected_typst = build_corrected_typst(orig_doc, use_edits)

    cor_sentences = [sent.text.strip() for sent in cor_doc.sents]
    max_pairs = min(len(orig_sentences), len(cor_sentences)) if orig_sentences else 0
    sentence_pairs = []
    for i in range(max_pairs):
        sentence_pairs.append({"original": orig_sentences[i], "corrected": cor_sentences[i]})

    correction_count = sum(eg["count"] for eg in errors_list)
    error_rate = round(correction_count / word_count * 100) if word_count > 0 else 0

    output = _build_output(student_id, original_text, corrected_text, word_count, student_info,
                           sentence_pairs, {"errors": errors_list, "uncategorised": uncategorised},
                           corrected_typst, error_rate, use_edits)
    output["metadata"] = metadata

    return _finalize_output(output, file_path)


def _build_output(student_id, original_text, corrected_text, word_count, student_info,
                  sentence_pairs, errant_analysis, corrected_typst, error_rate, edits):
    return {
        "student_id": student_id,
        "original_text": original_text,
        "corrected_text": corrected_text,
        "sentence_pairs": sentence_pairs,
        "errant_analysis": errant_analysis,
        "corrected_typst": corrected_typst,
        "error_rate": error_rate,
        "word_count": word_count,
        "name": student_info.get("name", ""),
        "class": student_info.get("class", ""),
    }


def _finalize_output(output, file_path):
    # Save without summary first
    write_output(output, file_path)
    # Generate summary (calls Mistral at temp 0.7)
    print("  Generating summary...")
    summary = generate_summary(output)
    output["summary"] = summary or ""
    print(f"  Summary: {summary[:80] if summary else '(empty)'}...")
    # Re-write with summary
    write_output(output, file_path)
    # Insert into Supabase
    insert_error_reports(output)
    return output


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


def main_batch(files):
    nlp = spacy.load("en_core_web_sm")
    annotator = errant.load("en")

    print(f"Processing {len(files)} file(s) with {MAX_WORKERS} workers...\n")

    results = []
    n_workers = min(MAX_WORKERS, len(files))
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        future_to_file = {
            executor.submit(process_file, f, nlp, annotator): f
            for f in files
        }
        for future in as_completed(future_to_file):
            f = future_to_file[future]
            try:
                r = future.result()
                if r:
                    results.append(r)
            except Exception as e:
                print(f"  Error processing {f.name}: {e}")

    print(f"\n{'='*50}")
    print(f"Done. Processed {len(results)}/{len(files)} files.")
    tc = sum(
        sum(e["count"] for e in r["errant_analysis"]["errors"])
        for r in results
    )
    print(f"Total errors detected: {tc}")
    print(f"Output: {LOCAL_WORKING_DIR}/")
    print(f"{'='*50}")


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
    if "--batch" in sys.argv:
        if not API_KEY:
            print("Error: OPENROUTER_API_KEY not set. Add it to .env or export it.")
            sys.exit(1)
        files = find_output_files()
        # Optional folder filter after --batch, e.g. --batch test2
        idx = sys.argv.index("--batch")
        folder_filter = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--") else None
        if folder_filter:
            files = [f for f in files if f.parent.name == folder_filter]
            if not files:
                print(f"No files found in folder '{folder_filter}'")
                sys.exit(1)
            print(f"Filtered to {len(files)} file(s) in '{folder_filter}'")
        if not files:
            print(f"No JSON files found in {OUTPUTS_DIR}/")
            print("Run ingest-images first to produce output files.")
            sys.exit(1)
        main_batch(files)
    else:
        main()
