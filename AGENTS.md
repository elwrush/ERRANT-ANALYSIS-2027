# AGENTS.md

## Project: ERRANT-ANALYSIS

Pipelines student handwriting images through OCR transcription (Gemini via OpenRouter), ERRANT grammatical error analysis, Supabase storage, and report generation.

## Slash commands

- `/ingest-papers` — Transcribe handwritten essays from `inputs/` subfolders using `google/gemini-2.5-flash-lite-preview-09-2025`
- `/local-errant-analysis` — Run ERRANT grammatical error analysis on transcribed essays

## Skills

- `.kilo/skills/ingest-images/SKILL.md` — Full workflow for handwriting image ingestion and transcription
- `.kilo/skills/errant-analysis/SKILL.md` — Full workflow for grammatical error analysis with ERRANT

## Python project

| Item | Path |
|------|------|
| Main script | `src/ingest.py` | `src/errant_analysis.py` |
| Tests | `tests/test_ingest.py` | `tests/test_errant.py` |
| Dependencies | `requirements.txt` |
| Linter | `ruff` |
| Test runner | `pytest` |

## Commands

```bash
# install dependencies
pip install -r requirements.txt

# run ingestion (interactive)
python src/ingest.py

# lint
ruff check src/ tests/

# test
pytest tests/ -v
```

## Input/output conventions

- Images: `inputs/{folder}/{student_id}_{page_num}.jpg`
- Output: `outputs/{folder}/{student_id}.json` with keys `student_id` and `student_text`
- Multi-page essays combined into a single JSON, pages joined with `<br>`
- API key: `OPENROUTER_API_KEY` in `.env` or environment

## Transcription rules (enforced by prompt)

- Verbatim — retain ALL errors (grammar, spelling, vocabulary)
- Student ID extracted from ID field on the page (not filename)
- `<br>` for paragraph breaks; no artificial line breaks
- Crossed-out text skipped; carat/insertion symbols resolved to natural flow
