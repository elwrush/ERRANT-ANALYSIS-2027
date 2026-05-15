# Skill: local-report

## Purpose

Generate a 4-page Typst booklet for each student after ERRANT analysis. Each booklet contains a personalized summary, error-rate line chart, original writing with error markup, corrected writing, and a detailed error breakdown table. Compiled to PDF automatically.

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

- Typst source: `outputs/{folder}/{dd-mm-yy}-{class}-{student_id}.typ`
- PDF: `PDF/{folder}/{dd-mm-yy}-{class}-{student_id}.pdf`
- Chart: `outputs/charts/{student_id}.png`

## Booklet structure (4 pages per student)

| Page | Content |
|------|---------|
| 1 | Header strap (ACT logo, Mathayom Program, Cambridge logo), personalised greeting, AI-generated summary, error-rate line chart |
| 2 | Original writing with corrections underlined |
| 3 | Corrected writing (clean) |
| 4 | Error breakdown table, total error rate, class info |

## Font

Base: Roboto 11pt. Header: Roboto 14pt bold. Falls back to system sans-serif if Roboto unavailable.

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No ERRANT outputs | Reports error, exits |
| No Supabase credentials | Runs charts without historical data (current point only) |
| No summary in JSON | Uses placeholder text |
| Typst compilation fails | Reports error, continues to next student |
| Chart generation fails | Reports error, continues without chart |

## Dependencies

- `typst 0.14+` (CLI installed separately)
- `matplotlib>=3.9` (for charts)
