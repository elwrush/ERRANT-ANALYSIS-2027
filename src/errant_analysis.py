#!/usr/bin/env python3
import os
import re
import sys
import json
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError, InternalServerError, AuthenticationError, BadRequestError
from _retry import RetryableError, NonRetryableError, retry
from generate_report import esc
import spacy
import errant
from rapidfuzz.distance import Levenshtein

load_dotenv(override=True)

API_KEY = os.environ.get("DEEPSEEK_API_KEY")

CORRECTION_MODEL = "deepseek-v4-flash"
SUMMARY_MODEL = "deepseek-v4-flash"

# Single DeepSeek client for both correction and summary
_client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com", max_retries=0)

OUTPUTS_DIR = Path("outputs")
LOCAL_WORKING_DIR = Path("local-working")
TEMPERATURE = 0.6

MAX_RETRIES = 3
REQUEST_TIMEOUT = 120
MULTI_TOKEN_THRESHOLD = 3
SUMMARY_TEMPERATURE = 0.8
MAX_WORKERS = 5
MAX_OUTPUT_TOKENS = 4096
MISSING_STUDENT_IDS: dict[str, list[str]] = {}

# Whole-text correction prompt — minimal edits: fix errors, don't rewrite
CORRECTION_PROMPT = """Fix the text below.

CRITICAL RULES:
- the writing must not be overly embellished or changed. You are a proofreader, not an editor. The acid test is that the outputted writing is perfectly grammatical, but semantically as similar as possible.
- Preserve original paragraph breaks
- Fix punctuation to academic English standards: no fused sentences, run-ons, comma splices, or stringy sentences.
- Fix missing words: add auxiliary verbs, articles, prepositions when needed. Take special care to ensure singular and plural nouns are used properly ("I enjoy playing drums", not "I enjoy playing drum".)
- At the most minimal level, repair gibberish. Do not do extravagant rewriting.

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
    return _call_api(CORRECTION_PROMPT.format(text=text), temperature)


def extract_correction(raw_response):
    """Extract the corrected text from the model's response to the whole-text prompt.
    Returns (corrected_text, []). Second element is always [] (no per-sentence explanations)."""
    if not raw_response:
        return None, []

    # Try to strip "Corrected text:" prefix if model included it
    m = re.search(r'(?:Corrected\s+text:)\s*(.+?)$', raw_response, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip(), []

    # No prefix found — use the entire response as the correction
    return raw_response.strip(), []


def _post_process_correction(corrected, original):
    """Apply deterministic fixes that the LLM may miss."""
    text = corrected
    # Convert standalone & to "and" (not part of HTML entities or other constructs)
    text = re.sub(r'(?<=\s)&(?=\s)', 'and', text)
    text = re.sub(r'(?<=\w)&(?=\s)', ' and', text)
    text = re.sub(r'(?<=\s)&(?=\w)', 'and ', text)
    # Common merged words: "world wide" → "worldwide" (keep "a lot" separate)
    text = re.sub(r'\bin the world wide\b', 'worldwide', text, flags=re.IGNORECASE)
    text = re.sub(r'\bthe world wide\b', 'worldwide', text, flags=re.IGNORECASE)
    text = re.sub(r'\bworld wide\b', 'worldwide', text, flags=re.IGNORECASE)
    # Clean up "the worldwide" → "worldwide"
    text = re.sub(r'\bthe worldwide\b', 'worldwide', text, flags=re.IGNORECASE)
    # Remove duplicate space from any edits above
    text = re.sub(r'\s+', ' ', text)
    return text


def correct_text(original_text, nlp_model):
    """Correct the full text in one pass using GPT-4.1-nano.
    Preserves paragraph breaks and sentence boundaries.
    Returns (corrected_full_text, [], [])."""
    tqdm.write(f"  Correcting full text ({len(original_text)} chars)...")
    
    raw = _call_api(CORRECTION_PROMPT.format(text=original_text), TEMPERATURE)
    if not raw:
        tqdm.write("  No correction received, using original text")
        return original_text, [], []
    
    corrected, _ = extract_correction(raw)
    if not corrected:
        tqdm.write("  Could not extract correction, using original text")
        return original_text, [], []
    
    corrected = corrected.strip()
    # Apply deterministic post-processing
    corrected = _post_process_correction(corrected, original_text)
    
    # Verify paragraph count matches
    orig_paras = [p for p in original_text.split("\n") if p.strip()]
    cor_paras = [p for p in corrected.split("\n") if p.strip()]
    
    if len(cor_paras) != len(orig_paras):
        tqdm.write(f"  Warning: paragraph count mismatch — original has {len(orig_paras)} paragraph(s), corrected has {len(cor_paras)}. Using corrected text anyway.")
    
    tqdm.write(f"  Corrected length: {len(corrected)} chars (original: {len(original_text)} chars)")
    return corrected, [], []


def call_model_custom(prompt_content, temperature=TEMPERATURE, model=None):
    """Call DeepSeek for correction. Thinking disabled so temperature is respected."""
    return _call_api(prompt_content, temperature, model=model)


@retry(max_retries=MAX_RETRIES)
def _call_api(content, temperature, model=None, *, disable_thinking=True):
    """Call the DeepSeek API. By default disables thinking mode so temperature is respected.
    Set disable_thinking=False for correction where model reasoning improves quality."""
    if not API_KEY:
        tqdm.write("  Error: no API key found (set DEEPSEEK_API_KEY in .env)")
        return None

    model_name = model if model else CORRECTION_MODEL

    try:
        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": content},
            ],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "timeout": REQUEST_TIMEOUT,
            "extra_body": {"user_id": "errant-pipeline"},
        }
        # Thinking mode defaults to enabled for ALL models. When enabled,
        # temperature/top_p/presence_penalty are IGNORED with no error.
        # We must explicitly disable thinking to use temperature for control.
        if disable_thinking:
            kwargs["extra_body"]["thinking"] = {"type": "disabled"}
        r = _client.chat.completions.create(**kwargs)
        result = r.choices[0].message.content
        if result:
            return result.strip()
        raise RetryableError("Empty response")
    except (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError):
        raise RetryableError("API error")
    except AuthenticationError:
        tqdm.write("  Error: invalid OpenRouter API key")
        return None
    except BadRequestError as e:
        tqdm.write(f"  Error: bad request  -  {e}")
        return None
    except RetryableError:
        raise
    except Exception as e:
        tqdm.write(f"  Unexpected error: {type(e).__name__}: {e}")
        raise NonRetryableError(str(e))


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



def lookup_student_info(student_id: str) -> dict:
    try:
        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ESL_KEY")
        if not supabase_url or not supabase_key:
            tqdm.write("  Supabase credentials not set  -  skipping classlist lookup")
            return {}
        client = create_client(supabase_url, supabase_key)
        result = client.table("classlists").select("student_id, name, class").eq("student_id", student_id).execute()
        if result.data and len(result.data) > 0:
            row = result.data[0]
            return {"class": row.get("class", ""), "name": row.get("name", "")}
        tqdm.write(f"  Warning: student {student_id} not found in Supabase classlists")
        return {}
    except Exception as e:
        tqdm.write(f"  Warning: could not query Supabase classlist: {e}")
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



SUMMARY_PROMPT_FMT = """You are an experienced ESL writing teacher. A student ({name}, CEFR B1-B2 level) wrote the original text below. A corrected version is also provided.

Identify the 3 most important errors in the student's original writing. Write your explanations and corrections to academic English standards — no comma splices, fused sentences, or sentence fragments.

Use this exact JSON format. The example errors are for illustration — replace with the student's actual errors:

{{
  "praise": "2-3 warm sentences about something specific they wrote. Keep it genuine. Do NOT use: shine, sparkle, glow, brilliant, amazing, incredible.",
  "segue": "One natural transition into the corrections, e.g. 'To improve even further, try to be aware of the following errors.'",
  "errors": [
    {{
      "name": "Spelling",
      "explanation": "You wrote \\"possesion\\" but the correct spelling is \\"possession.\\" Remember to double the 's' in the middle: poss-ess-ion."
    }},
    {{
      "name": "Sentence fragment",
      "explanation": "You wrote \\"In my free time.\\" with a full stop, but this group of words is not a complete sentence because it has no main verb. You cannot put a full stop here. Instead, connect it to your next sentence. For example: \\"In my free time, I love to play computer games with my friends.\\""
    }},
    {{
      "name": "Comma splice",
      "explanation": "You wrote \\"I love to play computer games with my friends, I am always learning\\" which is two complete thoughts joined by only a comma. Add a connecting word like 'and' after the comma: \\"I love to play computer games with my friends, and I am always learning.\\""
    }}
  ]
}}

CRITICAL RULES:
- Every phrase in double quotes within the explanation must appear verbatim in the original text below.
- Do NOT change, rephrase, or invent the student's words.
- Explain why it is wrong and how to fix it, with a natural example.

ORIGINAL TEXT:
{original_text}

CORRECTED TEXT:
{corrected_text}

Return ONLY the JSON object — no markdown, no code fences, no extra text."""


def _verify_structured_summary(summary_data, original_text, corrected_text):
    """Verify that every double-quoted phrase in each error's explanation
    appears verbatim in either the original or corrected text.
    Explanations naturally quote the student's error (from original) and
    show example fixes (from corrected). Both are legitimate.
    Returns list of warnings (empty = clean). Warnings do NOT trigger the
    fallback — only empty/unparseable summary_data does."""
    warnings = []
    
    if not isinstance(summary_data, dict):
        return ["summary_data is not a dict"]
    
    errors = summary_data.get("errors", [])
    for i, err in enumerate(errors):
        explanation = err.get("explanation", "")
        # Extract all double-quoted phrases from the explanation
        quoted_phrases = re.findall(r'"([^"]*)"', explanation)
        for j, phrase in enumerate(quoted_phrases):
            # Accept if in EITHER original or corrected
            if phrase not in original_text and phrase not in corrected_text:
                warnings.append(f"E{i}: phrase '{phrase[:80]}' not found verbatim in original or corrected")
    
    return warnings


def render_summary_to_text(summary_data, name):
    """Deterministically render structured summary data to readable text."""
    if not isinstance(summary_data, dict):
        return ""
    praise = summary_data.get("praise", "")
    segue = summary_data.get("segue", "")
    errors = summary_data.get("errors", [])
    
    parts = [f"*Dear {name},*", "", praise, ""]
    if segue:
        parts.append(segue)
        parts.append("")
    
    if errors:
        parts.append("*Here are some areas to work on:*")
        parts.append("")
        for err in errors:
            name_cat = err.get("name", "")
            explanation = err.get("explanation", "") or err.get("rule", "")
            parts.append(f"*{name_cat}:* {explanation}")
            parts.append("")
    
    return "\n".join(parts).strip()


def generate_summary(output: dict) -> dict:
    """Generate structured summary data from LLM.
    Returns {"summary": rendered_text_str, "summary_data": dict}."""
    name = output.get("name", "student")
    original_text = output.get("original_text", "")
    corrected_text = output.get("corrected_text", "")

    prompt = SUMMARY_PROMPT_FMT.format(
        name=name,
        original_text=original_text,
        corrected_text=corrected_text,
    )
    result = _call_api(prompt, SUMMARY_TEMPERATURE, model=SUMMARY_MODEL, disable_thinking=True)
    result = _sanitize_unicode(result or "")
    
    # Try to parse JSON from the response
    summary_data = None
    parsed = None
    import contextlib
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown fences
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
        if m:
            with contextlib.suppress(json.JSONDecodeError):
                parsed = json.loads(m.group(1))
        if not parsed:
            # Try to find JSON object in response
            m = re.search(r'\{.*\}', result, re.DOTALL)
            if m:
                with contextlib.suppress(json.JSONDecodeError):
                    parsed = json.loads(m.group(0))
    
    if isinstance(parsed, dict) and "praise" in parsed and "errors" in parsed:
        summary_data = parsed
        # Verify quotes — warn only, never reject. Pedagogical examples
        # may differ slightly from the corrected text (different punctuation,
        # truncated sentences for clarity). The model knows best how to explain.
        corrected_plain = output.get("corrected_text", "")
        warnings = _verify_structured_summary(summary_data, original_text, corrected_plain)
        for w in warnings[:3]:
            tqdm.write(f"  Summary verification (info only): {w}")
        
        rendered = render_summary_to_text(summary_data, name)
        tqdm.write(f"  Summary generated ({len(summary_data.get('errors', []))} errors)")
        output["summary_type"] = "llm"
        return {"summary": rendered, "summary_data": summary_data}
    
    # LLM didn't return valid JSON — return empty summary
    tqdm.write("  Could not parse structured summary — returning empty")
    output["summary_type"] = "empty"
    empty = {"summary": "", "summary_data": None}
    return empty


def insert_error_reports(output: dict):
    try:
        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ESL_KEY")
        if not supabase_url or not supabase_key:
            tqdm.write("  Supabase credentials not set  -  skipping error_reports insert")
            return
        client = create_client(supabase_url, supabase_key)
        row = {
            "student_id": output["student_id"],
            "class": output.get("class", ""),
            "name": output.get("name", ""),
            "error_percent": output["error_rate"] if output["error_rate"] is not None else None,
            "summary": output.get("summary", ""),
            "word_count": output.get("word_count", 0),
            "academic_year": 2027,
            "date": output.get("date_created", ""),
        }
        for col in ERROR_CODE_COLUMNS:
            row[col] = 0
        errors = output.get("errant_analysis", {}).get("errors", [])
        for e in errors:
            col = ERRANT_CODE_TO_COLUMN.get(e["type"])
            if col:
                row[col] = e["count"]
        client.table("error_reports").insert(row).execute()
        tqdm.write(f"  Inserted into error_reports for {output['student_id']} ({len(errors)} error types)")
    except Exception as e:
        tqdm.write(f"  Warning: could not insert into error_reports: {e}")


def post_classify_other(o_str, c_str):
    # Strip trailing punctuation so comparisons aren't thrown off by sentence boundaries
    trailing = ".,;:!?\"'"
    o_clean = o_str.strip().rstrip(trailing)
    c_clean = c_str.strip().rstrip(trailing)
    if not o_clean or not c_clean:
        # Empty original but model inserted a determiner → missing determiner
        if not o_clean and c_clean.lower() in {"the", "a", "an", "some", "any", "this", "that", "these", "those"}:
            return "M:DET"
        return "OTHER"

    o_lower = o_clean.lower().strip()
    c_lower = c_clean.lower().strip()

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


def build_corrected_typst(orig_doc, edits, original_text=""):
    """Build Typst markup from ERRANT edits. Paragraph breaks (\\n\\n)
    are preserved automatically via spaCy token whitespace (text_with_ws).
    No additional paragraph break insertion is needed."""
    edits = sorted(edits, key=lambda e: e.o_start)
    tokens = list(orig_doc)
    result_parts = []
    edit_idx = 0
    i = 0

    while i < len(tokens):
        if edit_idx < len(edits) and i == edits[edit_idx].o_start:
            edit = edits[edit_idx]
            # Deduplicate: skip if this edit is identical to the previous one (same position, same text)
            if edit_idx > 0:
                prev = edits[edit_idx - 1]
                if (edit.o_start == prev.o_start and edit.o_end == prev.o_end
                        and edit.o_str == prev.o_str and edit.c_str == prev.c_str
                        and edit.type == prev.type):
                    edit_idx += 1
                    continue
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


def align_sentences(orig_sentences, cor_sentences):
    """Align original and corrected sentences.

    Handles differing sentence counts:
    - When counts match: 1:1 pairing directly
    - When correction has fewer sentences (merges): best-match with grouping
    - When correction has more sentences (splits): best-match with grouping

    Uses RapidFuzz token_set_ratio for pairwise similarity.
    """
    from rapidfuzz import fuzz

    if not orig_sentences or not cor_sentences:
        return []

    # Single-sentence cases
    if len(orig_sentences) == 1 and len(cor_sentences) == 1:
        return [{"original": orig_sentences[0], "corrected": cor_sentences[0]}]

    # Equal count — use fuzzy matching to find best alignment
    # (direct 1:1 can be wrong when correction reorders sentence boundaries)
    if len(orig_sentences) == len(cor_sentences):
        # Try direct pairing first, check if all pairs have reasonable similarity
        direct_ok = True
        for o, c in zip(orig_sentences, cor_sentences):
            if fuzz.token_set_ratio(o, c) < 50:
                direct_ok = False
                break
        if direct_ok:
            return [
                {"original": o, "corrected": c}
                for o, c in zip(orig_sentences, cor_sentences)
            ]
        # Fall through to similarity-based matching below

    # Build similarity matrix
    n_orig = len(orig_sentences)
    n_cor = len(cor_sentences)
    sim = [[0.0] * n_cor for _ in range(n_orig)]
    for i, o in enumerate(orig_sentences):
        for j, c in enumerate(cor_sentences):
            sim[i][j] = fuzz.token_set_ratio(o, c) / 100.0

    # For each corrected sentence, find the best-matching original
    # and build groups of consecutive originals
    best_match = [0] * n_orig  # which corrected each orig maps to
    for i in range(n_orig):
        best_j = max(range(n_cor), key=lambda j: sim[i][j])
        best_match[i] = best_j

    # Group consecutive originals that map to the same corrected
    groups = []  # list of (orig_start, orig_end, cor_idx)
    i = 0
    while i < n_orig:
        cor_idx = best_match[i]
        start = i
        # Extend while consecutive originals map to the same corrected
        while i < n_orig and best_match[i] == cor_idx:
            i += 1
        groups.append((start, i, cor_idx))

    # Handle corrected sentences that no original maps to (splits)
    mapped_cors = {g[2] for g in groups}
    for j in range(n_cor):
        if j not in mapped_cors:
            # Find which group this split belongs to (nearest earlier orig)
            # or attach to nearest group
            best_i = max(range(n_orig), key=lambda i: sim[i][j])
            for g_idx, group_val in enumerate(groups):
                start, end, cor_idx = group_val[:3]
                if start <= best_i < end:
                    # Merge this corrected into the same group
                    groups[g_idx] = (start, end, cor_idx, True)  # mark as multi-cor
                    break

    # Build pairs from groups
    pairs = []
    for group in groups:
        if len(group) == 4:
            start, end, cor_idx, _ = group
            # Find ALL corrected sentences that map to this orig range
            cor_indices = set()
            for orig_i in range(start, end):
                for cor_j in range(n_cor):
                    if sim[orig_i][cor_j] > 0:
                        cor_indices.add(cor_j)
            cor_indices = sorted(cor_indices)
            orig_part = " ".join(orig_sentences[start:end])
            cor_part = " ".join(cor_sentences[j] for j in cor_indices)
        else:
            start, end, cor_idx = group
            orig_part = " ".join(orig_sentences[start:end])
            cor_part = cor_sentences[cor_idx]

        pairs.append({"original": orig_part, "corrected": cor_part})

    # If groups resulted in more pairs than corrected sentences,
    # merge adjacent pairs with the same corrected sentence
    merged = []
    for pair in pairs:
        if merged and merged[-1]["corrected"] == pair["corrected"]:
            merged[-1]["original"] += " " + pair["original"]
        else:
            merged.append(pair)
    pairs = merged

    return pairs


def classify_edits(edits, orig_tokens=None, cor_tokens=None):
    """Classify edits by type, building context-rich examples.
    If orig_tokens/cor_tokens are provided (lists from annotator.parse()),
    each example includes surrounding words for context in both the original
    and corrected versions."""
    error_groups = {}
    uncategorised = []
    dropped_edits = {"UNK": 0, "U:SPACE": 0, "UNK_examples": [], "U:SPACE_examples": []}

    for e in edits:
        e_type = e.type
        if e_type in ("OTHER", "R:OTHER") and e.o_toks and e.c_toks:
            e_type = post_classify_other(e.o_str, e.c_str)
        if e_type in ("UNK", "U:SPACE"):
            dropped_edits[e_type] += 1
            example = f"{str(e.o_str).strip()} -> {str(e.c_str).strip()}"
            if len(dropped_edits[f"{e_type}_examples"]) < 5:
                dropped_edits[f"{e_type}_examples"].append(example)
            continue
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

        # Build context original: show ~3 preceding words and ~3 following words
        context_original = example
        context_corrected = example
        if orig_tokens and e.o_toks:
            start = max(0, e.o_start - 3)
            end = min(len(orig_tokens), e.o_end + 3)
            before = " ".join(orig_tokens[start:e.o_start])
            after = " ".join(orig_tokens[e.o_end:end])
            punct_before = "..." if start > 0 else ""
            punct_after = "..." if end < len(orig_tokens) else ""
            o_str = e.o_str.strip() if e.o_str else ""
            c_str = e.c_str.strip() if e.c_str else ""
            context_original = f"{punct_before}{before} {o_str} {after}{punct_after}"

        # Build context corrected: show same span in the corrected text
        if cor_tokens and e.c_toks:
            c_start = max(0, e.c_start - 3)
            c_end = min(len(cor_tokens), e.c_end + 3)
            c_before = " ".join(cor_tokens[c_start:e.c_start])
            c_after = " ".join(cor_tokens[e.c_end:c_end])
            cpunct_before = "..." if c_start > 0 else ""
            cpunct_after = "..." if c_end < len(cor_tokens) else ""
            c_str = e.c_str.strip() if e.c_str else ""

            # For insertion edits with no corrected text, just use the corrected token
            if not c_str and e.c_toks:
                c_str = " ".join(t.text for t in e.c_toks)
            context_corrected = f"{cpunct_before}{c_before} {c_str} {c_after}{cpunct_after}"

        if e_type not in error_groups:
            error_groups[e_type] = {
                "type": e_type,
                "example": example,
                "context_original": context_original,
                "context_corrected": context_corrected,
                "count": 0,
            }
        error_groups[e_type]["count"] += 1

    errors_list = sorted(error_groups.values(), key=lambda x: x["count"], reverse=True)
    return errors_list, uncategorised, dropped_edits


def _reinsert_paragraph_breaks_llm(original_text, corrected_typst):
    """Re-insert paragraph breaks (\\n\\n) using a lightweight DeepSeek call.
    
    The correction model strips paragraph breaks. Rather than fragile deterministic
    text-matching, this asks the LLM to read both texts and fix the paragraphs
    like a human would — add breaks where they're missing, remove any stray ones
    that got misplaced."""
    if "\n\n" not in original_text:
        return corrected_typst

    prompt = (
        "I have two versions of a student's writing: the original (with correct "
        "paragraph breaks) and a corrected version (grammar fixed, but the paragraph "
        "breaks got jumbled up).\n\n"
        "Fix the corrected version so its paragraph breaks match the original. "
        "Add any missing breaks, remove any stray ones that landed in the wrong "
        "place, and leave everything else untouched.\n\n"
        "Original:\n"
        "---\n"
        f"{original_text}\n"
        "---\n\n"
        "Corrected (fix the paragraphs):\n"
        "---\n"
        f"{corrected_typst}\n"
        "---\n\n"
        "Return only the corrected text with proper paragraph breaks."
    )

    try:
        response = _client.chat.completions.create(
            model=SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
            timeout=30,
        )
        result = response.choices[0].message.content.strip()
        if result:
            return result
    except Exception as e:
        tqdm.write(f"  LLM paragraph break insertion failed: {e}")

    return corrected_typst


def process_file(file_path, nlp=None, annotator=None):
    tqdm.write(f"\n=== Processing: {file_path.relative_to(OUTPUTS_DIR)} ===")
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    student_id = data.get("student_id", "unknown")
    original_text = data.get("student_text", "").strip()
    word_count = data.get("word_count", 0)
    if word_count == 0 and original_text:
        word_count = len(original_text.split())

    if not original_text:
        tqdm.write("  Empty student_text, skipping.")
        return None

    student_info = lookup_student_info(student_id)
    if not student_info:
        source_images = data.get("source_images", [])
        entry = str(file_path)
        if source_images:
            entry += "  (source: " + ", ".join(source_images) + ")"
        MISSING_STUDENT_IDS.setdefault(student_id, []).append(entry)
        tqdm.write(f"  No classlist entry for {student_id}  -  name and class fields will be empty")
    if data.get("name"):
        student_info["name"] = data["name"]
    if data.get("class"):
        student_info["class"] = data["class"]
    record_id = data.get("record_id")
    submission_date = data.get("submission_date", "")
    topic = data.get("topic", "")
    tqdm.write(f"  Student: {student_id}")
    tqdm.write(f"  Student info: {student_info}")
    if topic:
        tqdm.write(f"  Topic: {topic}")

    if nlp is None:
        nlp = spacy.load("en_core_web_sm")
    orig_doc = nlp(original_text)
    orig_sentences = [sent.text.strip() for sent in orig_doc.sents]

    if annotator is None:
        annotator = errant.load("en")

    # Use annotator.parse() (whitespace-split tokenization) for ERRANT alignment
    orig_parse = annotator.parse(original_text)

    # ---- Step 1: Whole-text correction via GPT-4.1-nano ----
    corrected_text, llm_edits, _ = correct_text(original_text, nlp)

    corrected_text = corrected_text.strip()
    tqdm.write(f"  Corrected length: {len(corrected_text)} chars")

    output = _build_output(student_id, original_text, corrected_text, word_count, student_info, [],
                           {"errors": [], "uncategorised": []}, original_text, 0, [])
    output["record_id"] = record_id
    output["submission_date"] = submission_date
    output["topic"] = topic

    # Noop check
    if original_text.strip() == corrected_text.strip():
        tqdm.write("  No corrections needed  -  text unchanged by model.")
        output["metadata"] = build_metadata([], corrected_text, original_text)
        output["llm_edits"] = llm_edits
        return _finalize_output(output, file_path)

    # ---- Step 2: Run ERRANT diff on original vs corrected ----
    cor_parse = annotator.parse(corrected_text)
    edits = annotator.annotate(orig_parse, cor_parse)

    # ---- Step 3: Post-process edits ----
    edits = pre_split_edits(annotator, edits, orig_parse, cor_parse)
    orig_tokens = [t.text for t in orig_parse]
    cor_tokens = [t.text for t in cor_parse]
    errors_list, uncategorised, dropped_edits = classify_edits(edits, orig_tokens, cor_tokens)
    metadata = build_metadata(edits, corrected_text, original_text)

    # ---- Step 4: Build Typst markup and sentence pairs ----
    corrected_typst = build_corrected_typst(orig_parse, edits)

    # Re-insert paragraph breaks into corrected_typst (model strips them)
    if "\n\n" in original_text:
        corrected_typst = _reinsert_paragraph_breaks_llm(original_text, corrected_typst)

    # Split both texts into sentences for alignment
    cor_sentences = [sent.text.strip() for sent in nlp(corrected_text).sents]
    sentence_pairs = align_sentences(orig_sentences, cor_sentences)

    correction_count = sum(eg["count"] for eg in errors_list)
    if word_count > 0 and word_count < 40:
        error_rate = None
    else:
        error_rate = round(correction_count / word_count * 100) if word_count > 0 else 0

    output = _build_output(student_id, original_text, corrected_text, word_count, student_info,
                           sentence_pairs, {"errors": errors_list, "uncategorised": uncategorised, "dropped_edits": dropped_edits},
                           corrected_typst, error_rate, edits)
    output["record_id"] = record_id
    output["submission_date"] = submission_date
    output["topic"] = topic
    output["metadata"] = metadata
    output["llm_edits"] = llm_edits

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
    # Set date_created to today's date (YYYY-MM-DD)
    output["date_created"] = date.today().isoformat()
    # Save without summary first
    write_output(output, file_path)
    # Generate summary
    tqdm.write("  Generating summary...")
    summary_result = generate_summary(output)
    output["summary"] = summary_result.get("summary", "") if isinstance(summary_result, dict) else str(summary_result or "")
    output["summary_data"] = summary_result.get("summary_data") if isinstance(summary_result, dict) and summary_result.get("summary_data") else None
    preview = output["summary"][:80] if output["summary"] else "(empty)"
    stype = output.get("summary_type", "?")
    tqdm.write(f"  Summary ({stype}): {preview}...")
    # Re-write with summary
    write_output(output, file_path)
    # Insert into Supabase
    insert_error_reports(output)
    return output


def write_output(output, file_path):
    folder_name = file_path.parent.name
    record_id = output.get("record_id") or output.get("student_id", "unknown")
    output_filename = f"{folder_name}-{record_id}.json"
    output_path = LOCAL_WORKING_DIR / output_filename

    LOCAL_WORKING_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    tqdm.write(f"  Saved to: {output_path}")
    tc = sum(e["count"] for e in output["errant_analysis"]["errors"])
    er_display = f"{output['error_rate']}%" if output['error_rate'] is not None else "N/A"
    tqdm.write(f"  Total corrections: {tc}, rate: {er_display}")
    tqdm.write(f"  Uncat: {len(output['errant_analysis']['uncategorised'])}")
    if output["metadata"]["identity_check"]:
        tqdm.write("  Note: text required no corrections")
    if output["metadata"]["overcorrection_count"] > 0:
        tqdm.write(f"  Warning: {output['metadata']['overcorrection_count']} potential overcorrection(s) detected")

    return output


def main_batch(files):
    nlp = spacy.load("en_core_web_sm")
    annotator = errant.load("en")

    print(f"Processing {len(files)} file(s) with {MAX_WORKERS} workers...\n")

    results = []
    n_workers = min(MAX_WORKERS, len(files))
    with tqdm(total=len(files), unit="file", position=0, desc="Processing files") as pbar, \
         ThreadPoolExecutor(max_workers=n_workers) as executor:
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
                    tqdm.write(f"  Error processing {f.name}: {e}")
                pbar.update(1)
    tqdm.write(f"\n{'='*50}")
    tqdm.write(f"Done. Processed {len(results)}/{len(files)} files.")
    tc = sum(
        sum(e["count"] for e in r["errant_analysis"]["errors"])
        for r in results
    )
    print(f"Total errors detected: {tc}")
    if MISSING_STUDENT_IDS:
        missing_file = LOCAL_WORKING_DIR / "missing_student_ids.txt"
        lines = []
        for sid in sorted(MISSING_STUDENT_IDS):
            for fp in MISSING_STUDENT_IDS[sid]:
                lines.append(f"{sid} -> {fp}")
        missing_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n  {len(MISSING_STUDENT_IDS)} student(s) NOT found in Supabase classlist:")
        for sid in sorted(MISSING_STUDENT_IDS):
            print(f"    {sid}:")
            for fp in MISSING_STUDENT_IDS[sid]:
                print(f"      - {fp}")
        print(f"  Details saved to: {missing_file}")
        print("  Manually add these to Supabase classlists or update the JSON files with 'class' and 'name' fields.")
    print(f"Output: {LOCAL_WORKING_DIR}/")
    print(f"{'='*50}")


def main():
    if not API_KEY:
        print("Error: no API key found. Set DEEPSEEK_API_KEY in .env or environment.")
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
        er_display = f"{result['error_rate']}%" if result['error_rate'] is not None else "N/A"
        print(f"Error rate: {er_display}")
        print(f"{'='*50}")


if __name__ == "__main__":
    if "--batch" in sys.argv:
        if not API_KEY:
            print("Error: no API key found. Set DEEPSEEK_API_KEY in .env or environment.")
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

            # Ghost file check — block if GHOST_REPORT.txt exists
            ghost_report = OUTPUTS_DIR / folder_filter / "GHOST_REPORT.txt"
            if ghost_report.exists():
                print(f"\n{'!'*60}")
                print("  GHOST FILES STILL PRESENT — cannot proceed with ERRANT analysis")
                print(f"{'!'*60}")
                print(f"  Ghost report found: {ghost_report}")
                print("  These student IDs were not found in the classlist.")
                print("  Fix the IDs in the JSON files, then delete GHOST_REPORT.txt.")
                print("  Then re-run this command.")
                print(f"{'!'*60}")
                sys.exit(1)
        if not files:
            print(f"No JSON files found in {OUTPUTS_DIR}/")
            print("Run ingest-images first to produce output files.")
            sys.exit(1)
        main_batch(files)
    else:
        main()
