#!/usr/bin/env python3
"""Generate report PDFs from ERRANT analysis outputs."""
import base64
import mimetypes
import os
import re
import sys
import json
from datetime import date, datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from config import (
    LOCAL_WORKING_DIR, OUTPUTS_DIR, PDF_DIR,
    ERRANT_CODE_NAMES, B1_TARGET, B2_TARGET,
)

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
    name_esc = re.escape(name)
    text = re.sub(r'^(Dear|Hi)\s+' + name_esc + r'\s*,\s*\n*\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^(Dear|Hi)\s+\w+\s*,\s*\n*\s*', '', text, flags=re.IGNORECASE)
    text = text.lstrip("\n\r ")
    return text


def _file_to_data_uri(path):
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "application/octet-stream"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


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




def _format_date(dt_str):
    """Parse ISO date string and return 'Mon D' format e.g. 'May 5', 'Nov 6'."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %-d") if os.name != "nt" else dt.strftime("%b %d").lstrip("0").replace("  ", " ")
    except (ValueError, TypeError):
        return str(dt_str)[:8]





def _infer_cefr_level(class_name):
    """Infer CEFR level from class name. All M3+ classes are B2."""
    cn = class_name.upper()
    if cn.startswith("M3") or cn.startswith("M4") or cn.startswith("M5") or cn.startswith("M6"):
        return "B2"
    return "B1"


def generate_chart(student, data_points):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rates = [p["error_percent"] for p in data_points]
    # submission_date is populated from the date column in fetch_historical_data
    labels = [_format_date(p.get("submission_date", "")) for p in data_points]
    rates.append(student["error_rate"])
    labels.append(date.today().strftime("%b %-d") if os.name != "nt" else date.today().strftime("%b %d").lstrip("0").replace("  ", " "))

    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(labels, rates, marker="o", linestyle="-", linewidth=2, color="#000000")
    for i, (lb, r) in enumerate(zip(labels, rates)):
        if r is None:
            continue
        ax.annotate(f"{r}%", (lb, r), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8, color="#000000")

    level = _infer_cefr_level(student.get("class", ""))
    target = B1_TARGET if level == "B1" else B2_TARGET

    valid_rates = [r for r in rates if r is not None]
    max_val = max(max(valid_rates) + 10, target + 5) if valid_rates else target + 5
    ax.set_ylim(0, max_val)

    # Shade region below target in light gray
    ax.axhspan(0, target, xmin=0, xmax=1, facecolor="#cccccc", alpha=0.18)
    # Solid target line
    ax.axhline(y=target, color="#555555", linestyle="-", linewidth=1.5)

    # Target label at the end of the horizontal line (inline with line)
    ax.annotate(f"Target ({level})", xy=(1, target), xycoords=("axes fraction", "data"),
                xytext=(4, 0), textcoords="offset points", fontsize=8,
                color="#555555", fontweight="bold", va="center")

    # Target percentage on left y-axis
    yticks = list(ax.get_yticks())
    if target not in yticks:
        yticks.append(target)
        yticks.sort()
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{int(t)}%" if t == int(t) else f"{t}%" for t in yticks])

    ax.set_ylabel("Error rate (%)", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    sid = student["student_id"]
    chart_dir = OUTPUTS_DIR / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    path = chart_dir / f"{sid}.svg"
    fig.savefig(path, format="svg")
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
                .select("date, error_percent")\
                .eq("student_id", student_id)\
                .order("date")\
                .execute()
            if result.data:
                # Filter out NULL error_percent and rename date
                filtered = []
                for d in result.data:
                    if d.get("error_percent") is not None:
                        d.setdefault("submission_date", d.pop("date", ""))
                        filtered.append(d)
                return filtered[-5:]
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
        return unique[-5:]
    return []


def html_to_pdf(html_content: str, output_path: Path) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install playwright: pip install playwright && playwright install chromium")
        sys.exit(1)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.emulate_media(media="print")
        page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "1.5cm", "bottom": "1.5cm", "left": "1.5cm", "right": "1.5cm"},
            print_background=True,
        )
        browser.close()
    return output_path


def render_report(student: dict, template_path: Path, output_path: Path) -> Path:
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    tmpl = env.get_template(template_path.name)

    level = _infer_cefr_level(student.get("class", ""))
    target = B1_TARGET if level == "B1" else B2_TARGET

    summary_data = student.get("summary_data")
    summary_errors = []
    summary_segue = ""
    if isinstance(summary_data, dict):
        if summary_data.get("errors"):
            for err in summary_data["errors"]:
                summary_errors.append({
                    "name": err.get("name", ""),
                    "explanation": err.get("explanation", ""),
                })
        summary_segue = "Here are some language points to be aware of:" if summary_data.get("errors") else ""

    corrected_text = student.get("corrected_typst", student.get("corrected_text", ""))
    corrected_markup = corrected_text.replace("#underline[", "<u>").replace("]", "</u>")

    project_root = Path(__file__).resolve().parent.parent
    chart_path = project_root / "outputs" / "charts" / f"{student['student_id']}.svg"
    chart_path = chart_path.resolve()
    chart_data_uri = _file_to_data_uri(chart_path)

    logo_left = project_root / "images" / "cambridge.png"
    logo_right = project_root / "images" / "ACT.png"
    logo_left_uri = _file_to_data_uri(logo_left)
    logo_right_uri = _file_to_data_uri(logo_right)

    html = tmpl.render(
        student_id=student["student_id"],
        name=student.get("name", student["student_id"]),
        class_label=student.get("class", ""),
        word_count=student.get("word_count", 0),
        error_rate=student.get("error_rate"),
        cefr_level=level,
        target_rate=target,
        chart_path=chart_data_uri,
        summary_praise=summary_data.get("praise", "") if summary_data else "",
        summary_segue=summary_segue,
        summary_errors=summary_errors,
        corrected_markup=corrected_markup,
        original_text=student.get("original_text", ""),
        today=date.today().strftime("%B %d, %Y"),
        header_logo_left=logo_left_uri,
        header_logo_right=logo_right_uri,
    )
    return html_to_pdf(html, output_path)


def _interleave_pdfs(pdf_paths, output_path):
    import fitz
    docs = [fitz.open(str(p)) for p in pdf_paths]
    max_pages = max(len(d) for d in docs)
    out = fitz.open()
    for page_idx in range(max_pages):
        for doc in docs:
            if page_idx < len(doc):
                out.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
    out.save(str(output_path))
    out.close()
    for d in docs:
        d.close()


def _flatten_pdf(input_path, output_path):
    import subprocess
    try:
        subprocess.run(
            [
                "gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.7",
                "-dPDFSETTINGS=/printer",
                "-dEmbedAllFonts=true",
                "-dSubsetFonts=true",
                "-dDetectDuplicateImages=true",
                "-dCannotEmbedFontPolicy=/Warning",
                "-dColorConversionStrategy=/LeaveColorUnchanged",
                "-dNOOPTIMIZE=true",
                f"-sOutputFile={output_path}",
                str(input_path),
            ],
            check=True, capture_output=True, timeout=120,
        )
    except FileNotFoundError:
        print("  Warning: Ghostscript not found — skipping flatten")
        output_path.write_bytes(input_path.read_bytes())
    except subprocess.CalledProcessError as e:
        print(f"  Ghostscript failed (stderr): {e.stderr.decode(errors='replace')[:200]}")
        output_path.write_bytes(input_path.read_bytes())


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

    safe_class = class_name.replace("/", "-").replace("\\", "-")
    folder_output = OUTPUTS_DIR / (folder_name or safe_class)
    folder_output.mkdir(parents=True, exist_ok=True)
    pdf_dir = PDF_DIR / (folder_name or safe_class)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    template_path = Path(__file__).resolve().parent.parent / "templates" / "report.html"
    individual_pdfs = []
    for idx, student in enumerate(students):
        sid = student["student_id"]
        pdf_path = pdf_dir / f"{today}-{safe_class}-{sid}.pdf"
        try:
            render_report(student, template_path, pdf_path)
            print(f"  PDF ({idx+1}/{len(students)}): {pdf_path.name}")
            individual_pdfs.append(pdf_path)
        except Exception as e:
            print(f"  Error generating {sid}: {e}")

    # Merge all individual PDFs into one interleaved file (even for 1 student)
    merged_path = pdf_dir / f"{today}-{safe_class}-errant-report.pdf"
    try:
        _interleave_pdfs(individual_pdfs, merged_path)
        print(f"\n  Merged {len(individual_pdfs)} PDFs → {merged_path.name}")
        print("  (Pages interleaved for double-sided booklet printing)")

        # Delete individual PDFs
        for p in individual_pdfs:
            p.unlink()

        # Flatten with Ghostscript
        flat_path = pdf_dir / f"{today}-{safe_class}-errant-report-flat.pdf"
        _flatten_pdf(merged_path, flat_path)
        flat_path.replace(merged_path)
        print(f"  Flattened: {merged_path.name}")
    except Exception as e:
        print(f"  Error merging/flattening: {e}")

    print(f"\n{'='*50}")
    print(f"Done. {len(students)} student(s) in {pdf_dir}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
