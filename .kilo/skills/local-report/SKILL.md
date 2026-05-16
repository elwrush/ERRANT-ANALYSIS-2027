# Skill: local-report

## Purpose

Generate a combined Typst booklet from all ERRANT analysis outputs. All students are compiled into a single PDF, each occupying 4 pages (with blank pages as padding). Contains personalised greeting, AI-generated summary with human-readable error descriptions, error-rate line chart with CEFR target lines, original writing with underlined corrections, and error breakdown table.

## Files

| Item | Path |
|------|------|
| Report script | `src/generate_report.py` |
| ERRANT + summary script | `src/errant_analysis.py` |
| Supabase setup | `src/setup_error_analysis.py` |
| Images | `images/ACT.png`, `images/cambridge.png` |

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set environment variables:

| Variable | Value |
|----------|-------|
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ESL_KEY` | Service role key |

## Supabase table

The `error_reports` table stores historical error data for charting:

Columns: `id`, `created_at`, `student_id`, `class`, `name`, `error_percent`, `summary`.

## Workflow

1. Run ERRANT analysis (`/local-errant-analysis`) — this also generates summaries and inserts into `error_reports`
2. Run `python src/generate_report.py [folder_name]`

## Output

- Typst source: `outputs/{folder}/{dd-mm-yy}-{class}-combined.typ`
- PDF: `PDF/{folder}/{dd-mm-yy}-{class}-combined.pdf`
- Charts: `outputs/charts/{student_id}.png` (one per student)

## Page structure (4 pages per student)

| Page | Content |
|------|---------|
| 1 | Header strap (ACT 1.0cm, Mathayom Program, Cambridge 1.75cm), subhead `{name} - {id} - {class}`, personalised greeting (*Dear {name},*), AI-generated summary with guidance ("It is better to write..."), target-rate boilerplate, error-rate line chart with CEFR target line + gray shading |
| 2 | Your Writing with Corrections (underlined corrections, subhead "Corrections are underlined") |
| 3-4 | Blank pages (4-page minimum per student) |

Remaining pages blank-padded to reach 4-page minimum per student using Typst's `state`+`context` introspection (label anchor → `counter(page).at(label(anchor))` → `calc.rem-euclid`). No manual page counting.

## Font

Base: Roboto 14pt body (scales to ~10pt readable in A5 booklet when A4 folded). Title: 16pt. Header strap text: 14pt. Top margin: 5.0cm.

## ERRANT error descriptions

ERRANT codes are converted to human-readable descriptions using a mapping derived from `errant/en/classifier.py`. Broadened descriptions cover classification edge cases:

| Code | Description |
|------|-------------|
| R:SPELL | "Spelling or capitalisation mistakes" (covers 'i'→'I' case changes that ERRANT misclassifies) |
| R:ORTH | "Capitalisation, spacing, or punctuation errors" (covers punctuation edits ERRANT tags as orthography) |

Summary uses the top 3 errors, ranked by frequency (descending `count`). Each error includes explicit guidance: *"It is better to write '[correction]'"*.

## Chart

- X-axis: dates formatted as "May 5", "Nov 6" (max 5 data points: 4 historical + current)
- Y-axis: error rate %
- CEFR target line: B1=12% (M3), B2=7% (M4+). Solid horizontal line with "Target (B1/B2)" label. Gray `axhspan` alpha=0.18 below the line

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No ERRANT outputs | Reports error, exits |
| No Supabase credentials | Runs charts without historical data (current point only) |
| No summary in JSON | Uses placeholder text |
| Typst compilation fails | Reports compilation error |
| Chart generation fails | Reports error, continues without chart |

## Dependencies

- `typst 0.14+` (CLI installed separately)
- `matplotlib>=3.9` (for charts)
