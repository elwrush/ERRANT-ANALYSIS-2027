#!/usr/bin/env python3
"""Generate Typst report booklets from ERRANT analysis outputs."""
import os
import re
import sys
import json
import subprocess
from datetime import date
from pathlib import Path

LOCAL_WORKING_DIR = Path("local-working")
OUTPUTS_DIR = Path("outputs")
PDF_DIR = Path("PDF")


def esc(text):
    """Escape special characters for typst content blocks."""
    text = str(text)
    text = text.replace("\\", "\\\\")
    text = text.replace("#", "\\#")
    text = text.replace("$", "\\$")
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("~", "\\~")
    return text


def convert_markup(markup):
    """Convert <u>text</u> to #underline[text] for typst."""
    def _repl(m):
        return "#underline[" + esc(m.group(1)) + "]"
    result = re.sub(r"<u>(.*?)</u>", _repl, markup)
    result = result.replace("\n", " \\\n")
    return result


def build_typ_content(student):
    sid = student["student_id"]
    name = esc(student.get("name", sid))
    cls = esc(student.get("class", ""))
    err_rate = student["error_rate"]
    summary = student.get("summary", "No summary available.")
    ctext = esc(student.get("corrected_text", ""))
    markup = student.get("corrected_with_markup", "")
    errors = student.get("errant_analysis", {}).get("errors", [])
    marked = convert_markup(markup)

    rows = ""
    for e in errors[:8]:
        ex = esc(e.get("example", ""))
        rows += "    [" + e["type"] + "], [" + str(e["count"]) + "], [" + ex + "],\n"

    lines = []
    lines.append(r"#set page(paper: " + '"a4"' + ', margin: (x: 1.5cm, top: 2.5cm, bottom: 1.5cm))')
    lines.append(r"#set text(font: " + '"Roboto"' + ", size: 11pt)")
    lines.append(r"#set par(leading: 0.4em)")
    lines.append("")
    lines.append("#show: doc => {")
    lines.append("  set page(")
    lines.append("    header: context {")
    lines.append("      if counter(page).get().first() == 1 {")
    lines.append("        grid(")
    lines.append("          columns: (1fr, 2fr, 1fr),")
    lines.append("          align: (left + horizon, center + horizon, right + horizon),")
    lines.append('          image("/images/ACT.png", height: 1.2cm),')
    lines.append('          text(size: 14pt, weight: "bold")[Mathayom Program],')
    lines.append('          image("/images/cambridge.png", height: 1.2cm),')
    lines.append("        )")
    lines.append("        line(length: 100%, stroke: 1.5pt)")
    lines.append("      }")
    lines.append("    },")
    lines.append("  )")
    lines.append("  doc")
    lines.append("}")
    lines.append("")
    lines.append("#align(center, text(size: 13pt, weight: " + '"bold"' + ")[Writing Feedback Report])")
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
    lines.append("#align(center)[")
    lines.append('  #image("/outputs/charts/' + sid + '.png", width: 80%)')
    lines.append("]")
    lines.append("")
    lines.append("#pagebreak()")
    lines.append("")
    lines.append("#align(center, text(size: 13pt, weight: " + '"bold"' + ")[Your Writing])")
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("")
    lines.append(marked)
    lines.append("")
    lines.append("#pagebreak()")
    lines.append("")
    lines.append("#align(center, text(size: 13pt, weight: " + '"bold"' + ")[Corrected Writing])")
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("")
    lines.append(ctext)
    lines.append("")
    lines.append("#pagebreak()")
    lines.append("")
    lines.append("#align(center, text(size: 13pt, weight: " + '"bold"' + ")[Error Details])")
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("Error rate: " + str(err_rate) + "%  (class: " + cls + ")")
    lines.append("")
    lines.append("#v(0.5em)")
    lines.append("#table(")
    lines.append("  columns: (1fr, 1fr, 2fr),")
    lines.append("  stroke: 0.5pt,")
    lines.append("  table.header([*Type*], [*Count*], [*Example*]),")
    lines.append(rows)
    lines.append(")")

    return "\n".join(lines)


def generate_chart(student, data_points):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rates = [p["error_percent"] for p in data_points]
    labels = [str(p.get("created_at", f"P{i+1}"))[:5] for i, p in enumerate(data_points)]
    rates.append(student["error_rate"])
    labels.append("Now")

    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(labels, rates, marker="o", linestyle="-", linewidth=2, color="#2563eb")
    for i, (lb, r) in enumerate(zip(labels, rates)):
        ax.annotate(f"{r}%", (lb, r), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8, color="#2563eb")
    ax.set_ylim(0, max(rates) + 10)
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
                return result.data
    except Exception:
        pass
    # Fallback: local JSON file
    local_path = LOCAL_WORKING_DIR / "historical_data.json"
    if local_path.exists():
        all_data = json.loads(local_path.read_text(encoding="utf-8"))
        return [d for d in all_data if d["student_id"] == student_id]
    return []


def main():
    folder_name = sys.argv[1] if len(sys.argv) > 1 else None

    files = sorted(LOCAL_WORKING_DIR.rglob("*.json"))
    if folder_name:
        files = [f for f in files if f.stem.startswith(folder_name)]

    if not files:
        print(f"No ERRANT output files found in {LOCAL_WORKING_DIR}/")
        sys.exit(1)

    today = date.today().strftime("%d-%m-%y")
    generated = 0

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            student = json.load(f)

        sid = student["student_id"]
        class_name = student.get("class", "unknown")
        name = student.get("name", sid)
        print(f"\n  Generating report for {name} ({sid})...")

        if not student.get("summary"):
            student["summary"] = "Great effort! Keep practicing your writing skills regularly."
            print("    (no summary found in JSON — using placeholder)")

        data_points = fetch_historical_data(sid)
        print(f"    Historical data: {len(data_points)} point(s)")

        generate_chart(student, data_points)
        typ_content = build_typ_content(student)

        safe_class = class_name.replace("/", "-").replace("\\", "-")
        typ_filename = f"{today}-{safe_class}-{sid}.typ"
        pdf_filename = f"{today}-{safe_class}-{sid}.pdf"

        folder_output = OUTPUTS_DIR / (folder_name or safe_class)
        folder_output.mkdir(parents=True, exist_ok=True)
        typ_path = folder_output / typ_filename

        with open(typ_path, "w", encoding="utf-8") as f:
            f.write(typ_content)
        print(f"    Typst file: {typ_path}")

        pdf_dir = PDF_DIR / (folder_name or safe_class)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / pdf_filename

        try:
            result = subprocess.run(
                ["typst", "compile", "--root", ".", str(typ_path), str(pdf_path)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print(f"    PDF: {pdf_path}")
                generated += 1
            else:
                print(f"    Typst error: {result.stderr[:300]}")
        except Exception as e:
            print(f"    Compilation failed: {e}")

    print(f"\n{'='*50}")
    print(f"Done. Generated {generated}/{len(files)} PDF(s) in {PDF_DIR}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
