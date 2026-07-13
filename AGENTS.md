# AGENTS.md — ERRANT-ANALYSIS

Pipeline: OCR transcription (Gemini 2.5 Flash via OpenRouter) → grammatical error correction (DeepSeek V4 Flash) + ERRANT annotation → Supabase upsert → Jinja2+Playwright PDF reports.

## Stack

| Tool | Version / Config |
|------|------------------|
| Python | 3.14 |
| Linter | `ruff check src/ tests/` (config: `.ruff.toml`) |
| Tests | `pytest tests/ -v` (no coverage flag needed unless checking) |
| Coverage | `pytest --cov=src --cov-report=term` |
| PDF engine | **Playwright** (`pip install playwright && playwright install chromium`) — no Typst |
| Validation | `response_format` on all LLM calls; `model_validate()` before all JSON writes |
| Error codes | Canonical in `src/config.py` — all 43 ERRANT codes mapped to Supabase column names |

## Commands

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
ruff check src/ tests/
python -m pytest tests/ -v
```

## Pipeline stages

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| Ingestion | `src/ingest.py` | `inputs/{folder}/*.jpg` | `outputs/{folder}/{id}.json` |
| ERRANT | `src/errant_analysis.py` | Ingestion JSONs | `local-working/{folder}-{id}.json` |
| Batch upsert | `src/batch_errant_upsert.py` | `error_reports` rows (NULL error_percent) | Supabase upsert |
| Rename | `src/rename_json_files.py` | `local-working/` JSONs | `local-working/{id}.json` |
| Report | `src/generate_report.py` | Renamed JSONs | `PDF/{class}/` PDFs via Playwright |

Stage gates: preflight check (`src/preflight_check.py`) → ID sign-off (human) → proceed.

## Key files

- `src/config.py` — all shared constants, paths, model names, error code mappings
- `src/models.py` — Pydantic models: `IngestionOutput`, `ErrantOutput`, `ReportData`
- `templates/report.html` — Jinja2 template for PDF reports
- `scripts/archive/` — one-shot/exploratory scripts moved out of `src/`

## Archived scripts (NOT in src/)

`pilot_prep.py`, `query_class_mapping.py`, `query_skill_count.py`, `write_historical_data.py`, `test_models.py`, `add_word_count.py` — all moved to `scripts/archive/`.

## Env vars

`DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY` required. `SUPABASE_URL` + `SUPABASE_ESL_KEY` for Supabase operations.

## CEFR mapping

`_infer_cefr_level()` in `generate_report.py`: M3+ → B2 (target 7%), else → B1 (target 12%). The `class` field in output JSONs uses enrollment status (M2=active, M3=left) not academic level.

## Test files

| File | What it covers |
|------|---------------|
| `test_config.py` | Config paths, error code mapping completeness |
| `test_models.py` | All 3 Pydantic models with valid/invalid/edge data |
| `test_ingest.py` | JSON parsing, image preprocessing, response_format, IngestionOutput validation |
| `test_errant.py` | ERRANT detection, classification, align_sentences, metadata, response_format, ErrantOutput validation |
| `test_report.py` | Jinja2 template rendering, chart generation, historical data, CEFR inference |
| `test_retry.py` | Retry decorator (RetryableError, NonRetryableError, max_retries) |
| `test_dependency_graph.py` | Module import depth, circular dependency check |
| `test_rename_json_files.py` | Student ID extraction, Supabase lookup, renaming |
| `test_smoke.py` | Import + public function check for all remaining modules |
