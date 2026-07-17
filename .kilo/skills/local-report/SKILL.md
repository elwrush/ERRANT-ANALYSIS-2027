# Skill: local-report

## Purpose

Generate student feedback report PDFs from ERRANT analysis outputs using **Jinja2 + Playwright** (no Typst). Each student gets a 2-page report with personalised praise, error breakdown, SVG error-rate trend chart (last 5 data points from Supabase), corrected text with underline markup, and the original text. All images (logos, chart) are embedded as base64 data URIs.

## Usage

```bash
python src/generate_report.py "FOLDER_NAME"
```

Processes all ERRANT outputs in `local-working/` matching `<folder>-<student_id>.json`, generates PDFs to `PDF/{folder}/`.

## Agent workflow

Use the `question` tool to ask the user which folder, then run:

```bash
python src/generate_report.py "FOLDER_NAME"
```

### Interleaved merge (always)

All student PDFs are **always** merged into a single interleaved file (even for 1 student). Pages are interleaved for double-sided booklet printing:
- Student A pg1, Student B pg1, Student A pg2, Student B pg2, ...
- After cutting down the middle, each student's pages form their own booklet
- Individual per-student PDFs are **deleted** after merge

### Ghostscript flattening

The merged PDF is flattened with Ghostscript (`pdfwrite` device, `CompatibilityLevel=1.7`, `/printer` settings, no color conversion) so Adobe/Acrobat doesn't re-process transparencies. Falls back to unflattened copy with a warning if `gs` is not on PATH.

## Output

- `PDF/{folder}/{dd-mm-yy}-{class}-errant-report.pdf` — single interleaved, flattened PDF
- `outputs/charts/{student_id}.svg` — per-student error rate SVG chart (black line, grayscale-safe, target line inline-annotated)

## Template

`templates/report.html` — Jinja2 template with C·E·L Mathayom masthead (Cambridge logo left, ACT right), Roboto font, A4 page size.

## CEFR benchmarks

Targets (aspirational classroom targets, not CEFR-mandated):
- B1: 15% error rate
- B2: 10% error rate

## Prerequisites

```bash
pip install -r requirements.txt
```

Env vars: `SUPABASE_URL`, `SUPABASE_ESL_KEY` (for historical error chart data from `error_reports` table).
