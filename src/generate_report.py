#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Typst report booklets from ERRANT analysis outputs."""
import os
import re
import sys
import json
import subprocess
from datetime import date, datetime
from pathlib import Path

LOCAL_WORKING_DIR = Path("local-working")
OUTPUTS_DIR = Path("outputs")
PDF_DIR = Path("PDF")

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
    "R:DET": "Problems with determiners (a, an, the)",
    "R:CONJ": "Problems with conjunctions",
    "R:PART": "Problems with particles",
    "R:PUNCT": "Problems with punctuation",
    # Spelling and orthography
    "R:SPELL": "Spelling or capitalisation mistakes",
    "R:ORTH": "Capitalisation, spacing, or punctuation errors",
    "R:MORPH": "Problems with word formation",
    # Structure
    "R:WO": "Problems with word order",
    "R:CONTR": "Problems with contractions",
    # Missing error codes
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
    # Unnecessary error codes
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


def human_error_type(err_type):
    if err_type in ERRANT_CODE_NAMES:
        return ERRANT_CODE_NAMES[err_type]
    prefix = err_type[:2] if len(err_type) > 1 and err_type[1] == ":" else ""
    body = err_type[2:] if prefix else err_type
    if body in ERRANT_CODE_NAMES:
        desc = ERRANT_CODE_NAMES[body]
        if prefix == "M:":
            return f"Missing: {desc.lower()}"
        if prefix == "U:":
            return f"Unnecessary: {desc.lower()}"
        return desc
    return err_type


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


def _strip_salutation(text, name):
    """Remove leading 'Hi Name,' or 'Dear Name,' salutation from summary text."""
    name_esc = re.escape(name)
    text = re.sub(r'^(Dear|Hi)\s+' + name_esc + r'\s*,\s*\n*\s*', '', text, flags=re.IGNORECASE)
    # Also handle trailing comma variants and 'student' generic
    text = re.sub(r'^(Dear|Hi)\s+\w+\s*,\s*\n*\s*', '', text, flags=re.IGNORECASE)
    # Remove leading blank lines after stripping salutation
    text = text.lstrip("\n\r ")
    return text


def _bold_error_headers(text):
    """Normalise -- to : in error headers, and add bold if not already present."""
    # Normalise -- to : (for legacy summaries that use em dashes)
    text = re.sub(r'(\([A-Z]+(?::[A-Z]+)*\))\s*--', r'\1:', text)
    # Only wrap in bold if no bold markers already present
    if '*(' not in text:
        text = re.sub(r'^(\d+\.\s+)(.*?\([A-Z]+(?::[A-Z]+)*\):)', r'\1*\2* ', text, flags=re.MULTILINE)
    return text


def _replace_errant_codes(text):
    """Replace raw ERRANT codes like 'R:NOUN:' with bold human-readable description plus code in brackets.
    Uses longest-first matching with negative lookbehind to skip codes already in brackets."""
    codes = sorted(ERRANT_CODE_NAMES.keys(), key=len, reverse=True)
    for code in codes:
        desc = ERRANT_CODE_NAMES[code]
        # Match code followed by colon, whitespace, or dash (but NOT preceded by open paren,
        # which means it's already been replaced and bracketed)
        pattern = r'(?<!\()' + re.escape(code) + r'(?=[:：\s\-–—])'
        # Wrap description in * for Typst bold, then append code in parentheses
        replacement = f'*{desc}* ({code})'
        text = re.sub(pattern, replacement, text)
    return text


def esc(text):
    text = str(text)
    text = _sanitize_unicode(text)
    text = text.replace("\\", "\\\\")
    text = text.replace("#", "\\#")
    text = text.replace("$", "\\$")
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("~", "\\~")
    return text


def esc_typst_markup(text):
    """Escape text that already contains Typst commands like #underline[...].
    Only sanitize Unicode — leave # [ ] escaped characters intact for Typst compilation.
    Guard against rare cases where student text contains Typst-special characters."""
    text = str(text)
    text = _sanitize_unicode(text)
    # Only escape backslash and dollar — other Typst special chars (#[]{~}*)
    # are handled by the LLM producing valid markup, and are vanishingly rare
    # in Thai EFL student writing.
    text = text.replace("\\", "\\\\")
    text = text.replace("$", "\\$")
    return text


def _format_summary_paragraph(summary_text):
    """Convert analysis summary into displayable form.
    
    Two formats:
    1. Old ERRANT format: numbered items like "1. *Problems with verb tense...*"
       — displayed as-is with Typst formatting
    2. New flat format: 3 bullet points — converted to coherent paragraph
    """
    # Check if summary is already formatted with numbered items (old ERRANT style)
    if re.search(r'^\d+\.\s+\*', summary_text, re.MULTILINE):
        return summary_text  # Already well-formatted, display as-is
    
    points = [p.strip() for p in summary_text.split('\n') if p.strip()]
    if not points:
        return "Continue practicing your writing skills regularly."
    
    # Strip leading action verbs like "Work on", "Improve", "Expand", "Focus on", "Practice"
    LEADING_VERBS = r'^(Work on|Improve|Expand|Focus on|Practice|Review|Study|Try to|Remember to)\s+'
    cleaned = []
    for p in points:
        p_clean = re.sub(LEADING_VERBS, '', p, flags=re.IGNORECASE)
        p_clean = p_clean[0].lower() + p_clean[1:] if p_clean else p
        cleaned.append(p_clean)
    
    if len(cleaned) >= 3:
        return (f"In your writing, I noticed: {cleaned[0]} "
                f"You should also work on {cleaned[1]} "
                f"Additionally, {cleaned[2]}")
    elif len(cleaned) == 2:
        return (f"In your writing, I noticed: {cleaned[0]} "
                f"You should also work on {cleaned[1]}")
    else:
        return f"In your writing, I noticed: {cleaned[0]}"


def _summarize_errors(errors):
    """Return a human-readable breakdown of errors by supercategory and CEFR level."""
    by_cat = {}
    by_level = {}
    for e in errors:
        cat = e.get("supercategory", "OTHER").replace("_", " ").title()
        by_cat[cat] = by_cat.get(cat, 0) + 1
        lv = e.get("cefr_level", "?")
        by_level[lv] = by_level.get(lv, 0) + 1
    
    total = len(errors)
    level_parts = [f"{count} at {lv}" for lv, count in sorted(by_level.items())]
    level_str = ", ".join(level_parts) if level_parts else "unclassified"
    
    cat_parts = sorted(by_cat.items(), key=lambda x: -x[1])
    cat_str = ", ".join(f"{name} ({count})" for name, count in cat_parts)
    
    return total, level_str, cat_str


def build_typ_header():
    lines = []
    lines.append('#set page(paper: "a4", margin: (x: 1.5cm, top: 2.0cm, bottom: 1.5cm))')
    lines.append('#set text(font: "Roboto", size: 14pt)')
    lines.append('#set par(leading: 0.5em)')
    lines.append("")
    return "\n".join(lines)


def build_student_block(student, idx):
    sid = student["student_id"]
    raw_name = student.get("name", sid)
    name = esc(raw_name)
    cls = esc(student.get("class", ""))
    summary = student.get("summary", "No summary available.")
    # Clean summary: sanitize unicode, no ERRANT codes in new format
    summary = _sanitize_unicode(summary)
    summary = _strip_salutation(summary, raw_name)
    summary = _replace_errant_codes(summary)
    summary = esc(summary)

    level = _infer_cefr_level(student.get("class", ""))
    target = B1_TARGET if level == "B1" else B2_TARGET

    # Use corrected_typst if available, else use corrected_text as plain text
    markup = student.get("corrected_typst", student.get("corrected_with_markup", student.get("corrected_text", "")))
    marked = markup.replace("\n", "\n\n")

    # Original uncorrected text
    orig = student.get("original_text", "")
    orig_escaped = esc(orig).replace("\n", "\n\n")

    lines = []

    # Masthead grid with logos and separator line
    lines.append('#grid(')
    lines.append('  columns: (0.8fr, 2fr, 1.2fr),')
    lines.append('  align: (left + horizon, center + horizon, right + horizon),')
    lines.append('  image("/images/ACT.png", height: 1.56cm),')
    lines.append('  text(size: 18pt, weight: "bold")[Mathayom Program],')
    lines.append('  image("/images/cambridge.png", height: 2.2cm),')
    lines.append(')')
    lines.append('#line(length: 100%, stroke: 1.0pt)')
    lines.append('')
    lines.append('#v(1em)')
    lines.append('')

    lines.append('#align(center, text(size: 16pt, weight: "bold")[Writing Accuracy Feedback Report])')
    lines.append(f'#align(center, text(size: 11pt)[{raw_name} - {sid} - {cls}])')
    lines.append("")
    lines.append("#v(1em)")
    lines.append("")
    lines.append("*Dear " + name + ',*')
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("")
    lines.append(summary)
    lines.append("")
    lines.append("#v(1em)")
    lines.append("")
    # Boilerplate target explanation
    lines.append('#align(center)[')
    lines.append(f'  #text(size: 11pt)[The solid line in the chart below shows the {level} target error rate ({target}%). Your goal is to keep your error rate below this line. The chart tracks your progress over time.]')
    lines.append("]")
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("")
    lines.append('#align(center)[')
    lines.append('  #image("/outputs/charts/' + sid + '.png", width: 80%)')
    lines.append("]")
    lines.append("")
    lines.append('#v(1em)')
    lines.append("")
    lines.append("#pagebreak()")
    lines.append("")
    lines.append('#align(center, text(size: 16pt, weight: "bold")[Your Writing with Corrections])')
    lines.append('#text(size: 11pt)[I scanned your writing for errors and underlined the corrections below. Carefully comparing the corrected and original versions will help you become more aware of common mistakes\\')
    lines.append('and improve your writing skills.]')
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("")
    lines.append(marked)
    lines.append("")
    lines.append("#v(2em)")
    lines.append("")
    lines.append('#align(center, text(size: 16pt, weight: "bold")[Your Original Writing (Uncorrected)])')
    lines.append('#align(center, text(size: 11pt)[Below is your original writing exactly as you submitted it, before any corrections were applied. Compare it with the corrected version above.])')
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("")
    lines.append(orig_escaped)
    lines.append("")
    # Pad to exactly 4 pages: zero-width invisible anchor + blank pages
    lines.append(f'#box(width: 0pt) <pad-anchor-{idx}>')
    lines.append('#context {')
    lines.append(f'  let num = counter(page).at(label("pad-anchor-{idx}")).first()')
    lines.append('  for _ in range(calc.rem-euclid(4 - num, 4)) {')
    lines.append('    page([])')
    lines.append('  }')
    lines.append('}')

    return "\n".join(lines) + "\n"


def _format_date(dt_str):
    """Parse ISO date string and return 'Mon D' format e.g. 'May 5', 'Nov 6'."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %-d") if os.name != "nt" else dt.strftime("%b %d").lstrip("0").replace("  ", " ")
    except (ValueError, TypeError):
        return str(dt_str)[:8]


# B1 and B2 target error rates based on ESL writing assessment research
# B1 (intermediate): ~12% — learners produce simple connected text
# B2 (upper intermediate): ~7% — learners produce clear, detailed text
B1_TARGET = 12
B2_TARGET = 7


def _infer_cefr_level(class_name):
    """Infer CEFR level from class name. M3 ~ B1, M4+ ~ B2, default B1."""
    cn = class_name.upper()
    if cn.startswith("M4") or cn.startswith("M5") or cn.startswith("M6"):
        return "B2"
    if cn.startswith("M3"):
        return "B1"
    return "B1"


def generate_chart(student, data_points):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rates = [p["error_percent"] for p in data_points]
    # Try submission_date first (fallback), then created_at (Supabase)
    labels = [_format_date(p.get("submission_date", p.get("created_at", ""))) for p in data_points]
    rates.append(student["error_rate"])
    labels.append(date.today().strftime("%b %-d") if os.name != "nt" else date.today().strftime("%b %d").lstrip("0").replace("  ", " "))

    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(labels, rates, marker="o", linestyle="-", linewidth=2, color="#2563eb")
    for i, (lb, r) in enumerate(zip(labels, rates)):
        ax.annotate(f"{r}%", (lb, r), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8, color="#2563eb")

    level = _infer_cefr_level(student.get("class", ""))
    target = B1_TARGET if level == "B1" else B2_TARGET
    label = f"Target ({level})"

    max_val = max(max(rates) + 10, target + 5)
    ax.set_ylim(0, max_val)

    # Shade region below target in light gray
    ax.axhspan(0, target, xmin=0, xmax=1, facecolor="#cccccc", alpha=0.18)
    # Solid target line
    ax.axhline(y=target, color="#555555", linestyle="-", linewidth=1.5)
    ax.annotate(label, xy=(1, target), xycoords=("axes fraction", "data"),
                xytext=(5, -8), textcoords="offset points", fontsize=8,
                color="#555555", fontweight="bold", va="top")

    ax.set_ylabel("Error rate (%)", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    sid = student["student_id"]
    chart_dir = OUTPUTS_DIR / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    path = chart_dir / f"{sid}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Chart saved: {path}")
    return path


def fetch_historical_data(student_id):
    from dotenv import load_dotenv
    load_dotenv()
    # Try Supabase first
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ESL_KEY")
        if url and key:
            client = create_client(url, key)
            result = client.table("error_reports")\
                .select("created_at, error_percent")\
                .eq("student_id", student_id)\
                .order("created_at")\
                .execute()
            if result.data:
                # Rename created_at to submission_date for uniform handling
                for d in result.data:
                    d.setdefault("submission_date", d.pop("created_at", ""))
                return result.data[-4:]
    except Exception:
        pass
    # Fallback: local JSON file
    local_path = LOCAL_WORKING_DIR / "historical_data.json"
    if local_path.exists():
        all_data = json.loads(local_path.read_text(encoding="utf-8"))
        entries = [d for d in all_data if d["student_id"] == student_id]
        # Deduplicate by (submission_date, error_percent) keeping last occurrence
        seen = {}
        for e in entries:
            key = (e.get("submission_date", ""), e.get("error_percent"))
            seen[key] = e
        unique = list(seen.values())
        unique.sort(key=lambda x: x.get("submission_date", ""))
        return unique[-4:]
    return []


def main():
    folder_name = sys.argv[1] if len(sys.argv) > 1 else None

    files = sorted(LOCAL_WORKING_DIR.rglob("*.json"))
    if folder_name:
        files = [f for f in files if f.stem.startswith(folder_name + "-")]

    if not files:
        print(f"No analysis output files found in {LOCAL_WORKING_DIR}/")
        sys.exit(1)

    today = date.today().strftime("%d-%m-%y")
    class_name = "combined"
    students = []

    for file_path in files:
        with open(file_path, encoding="utf-8") as f:
            student = json.load(f)

        sid = student["student_id"]
        cls = student.get("class", "unknown")
        name = student.get("name", sid)
        print(f"\n  Preparing report for {name} ({sid})...")

        if not student.get("summary"):
            student["summary"] = "Great effort! Keep practicing your writing skills regularly."
            print("    (no summary found in JSON — using placeholder)")

        data_points = fetch_historical_data(sid)
        print(f"    Historical data: {len(data_points)} point(s)")

        generate_chart(student, data_points)
        class_name = cls.replace("/", "-").replace("\\", "-")
        students.append(student)

    if not students:
        print("No students to process.")
        sys.exit(1)

    # Build single combined typst document
    all_blocks = [build_typ_header()]
    for idx, student in enumerate(students):
        all_blocks.append(build_student_block(student, idx))

    typ_content = "\n".join(all_blocks)

    safe_class = class_name.replace("/", "-").replace("\\", "-")
    typ_filename = f"{today}-{safe_class}-combined.typ"
    pdf_filename = f"{today}-{safe_class}-combined.pdf"

    folder_output = OUTPUTS_DIR / (folder_name or safe_class)
    folder_output.mkdir(parents=True, exist_ok=True)
    typ_path = folder_output / typ_filename

    with open(typ_path, "w", encoding="utf-8") as f:
        f.write(typ_content)
    print(f"\nTypst source: {typ_path}")

    pdf_dir = PDF_DIR / (folder_name or safe_class)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / pdf_filename

    generated = 0
    try:
        result = subprocess.run(
            ["typst", "compile", "--root", ".", str(typ_path), str(pdf_path)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"  PDF: {pdf_path}")
            generated = 1
        else:
            print(f"  Typst error: {result.stderr[:500]}")
    except Exception as e:
        print(f"  Compilation failed: {e}")

    print(f"\n{'='*50}")
    print(f"Done. Generated {generated} file(s) with {len(students)} student(s) in {PDF_DIR}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
