# Skill: local-report

## Purpose

Generate Typst report booklets from ERRANT analysis outputs. Each student gets a 4-page booklet with personalised feedback, error chart, corrected/uncorrected writing, and error breakdown — compiled to PDF.

## Usage

```bash
python src/generate_report.py "M2-5A BASELINE"
```

Processes all ERRANT outputs in `local-working/` for the given folder, generates PDFs to `PDF/{folder}/`.

## Agent workflow

Use the `question` tool to ask the user which folder, then run:

**Before running the report generator, validate Typst syntax:**

```bash
# No standalone .typ files — Typst is built in Python f-strings in generate_report.py.
# The agent validates each .typ snippet inline before assembling:
echo "$typstContent" | python "$env:USERPROFILE\.kilo\scripts\typst_check.py" -
```

```bash
python src/generate_report.py "FOLDER_NAME"
```

Consult the global Typst troubleshooting reference at `C:\Users\elwru\.config\kilo\reference\typst-troubleshooting.md` for known issues with page geometry, context blocks, pad-to-four, paragraph breaks, and other Typst traps encountered in report generation.

## Output

- `PDF/{folder}/{dd-mm-yy}-{class}-combined.pdf` — compiled booklet (individual per-student PDFs compiled separately then merged)
- `outputs/charts/{student_id}.png` — per-student error rate chart

## Prerequisites

```bash
pip install -r requirements.txt
```

Env vars: `SUPABASE_URL`, `SUPABASE_ESL_KEY` (for historical error chart data).
Typst CLI 0.14+ must be installed separately and on PATH.
