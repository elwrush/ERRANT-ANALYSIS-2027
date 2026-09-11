---
name: local-report
description: 'Generate per-student ERRANT feedback report PDFs with Jinja2 + Playwright (SVG charts, base64 opaque images, standalone single files, no Ghostscript). Use when asked to generate or refresh student feedback reports/PDFs, run src/generate_report.py, or render a class folder to PDF/{folder}/.'
license: MIT
compatibility:
  - python3
  - pip install -r requirements.txt
  - Playwright browsers installed
  - SUPABASE_URL + SUPABASE_ESL_KEY (for trend charts)
metadata:
  author: C.E.L Mathayom / ACT
  version: 1.0.0
---

# Skill: local-report

## Purpose

Generate student feedback report PDFs from ERRANT analysis outputs using **Jinja2 + Playwright** (no Typst). Each student gets a 2-page report with personalised praise, error breakdown, SVG error-rate trend chart (last 5 data points from Supabase), corrected text with underline markup, and the original text. All images (logos, chart) are embedded as base64 data URIs.

## Usage

```bash
python src/generate_report.py "FOLDER_NAME"
```

Processes all ERRANT outputs in `local-working/` matching `<folder>-<student_id>.json`, generates one standalone PDF per student to `PDF/{folder}/`.

## Agent workflow

Use the `question` tool to ask the user which folder, then run:

```bash
python src/generate_report.py "FOLDER_NAME"
```

### Standalone single files (always)

Each student gets **one standalone PDF**. There is no merge, no concatenation, no interleaving, and no combined `*-errant-report.pdf`. Pages are **not** padded to a multiple of four. Individual PDFs are retained on disk.

### Opaque images, no flattening

Transparency is removed at the source so Adobe/Acrobat never needs to flatten:
- Raster logos are composited onto white and embedded as opaque RGB PNGs (`src/image_utils.py`).
- Charts are alpha-free SVG (opaque fills + opaque white background).

Ghostscript is **not** used anywhere in the pipeline.

## Output

- `PDF/{folder}/{dd-mm-yy}-{HHMM}-{class}-{sid}.pdf` — one standalone PDF per student
- `outputs/charts/{student_id}.svg` — per-student error rate SVG chart (black line, grayscale-safe, target line inline-annotated, no transparency)

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

Env vars (zsh env — `~/.env` sourced by `~/.zshrc`): `SUPABASE_URL`, `SUPABASE_ESL_KEY` (for historical error chart data from `error_reports` table).
