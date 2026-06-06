# AGENTS.md

## Project: ERRANT-ANALYSIS

Full ERRANT analysis pipeline: ingests student handwriting images via OCR transcription (Gemini via OpenRouter), runs grammatical error analysis with DeepSeek V4 Flash + ERRANT, uploads structured reports to Supabase, and generates Typst report booklets with PDF output.

## Shell: Windows PowerShell 5.1

This project runs on Windows PowerShell 5.1.

## Slash commands & skills

| Command | Skill file | Description |
|---------|------------|-------------|
| `/ingest-images` | `.kilo/skills/ingest-images/SKILL.md` | Transcribe handwritten essays from images via Gemini on OpenRouter |
| `/errant-analysis` | `.kilo/skills/errant-analysis/SKILL.md` | Grammatical error correction and analysis with DeepSeek + ERRANT |
| `/git-backup` | `.kilo/skills/git-backup/SKILL.md` | Diff, commit with verbose message, and push to remote |
| `/rename-json-files` | `.kilo/skills/rename-json-files/SKILL.md` | Rename ERRANT outputs to `student_id.json`, validated against Supabase classlist |
| `/review` | — (self-contained) | Run lint, tests, and quality review of uncommitted changes |
| `/local-report` | `.kilo/skills/local-report/SKILL.md` | Generate Typst report booklets from ERRANT analysis with PDF output |
| `/context7` | `.kilo/skills/context7-docs/SKILL.md` | Search library documentation via Context7 API (global skill) |

### Global skills (no dedicated command)

- `tavily-websearch` (`.kilo/skills/tavily-websearch/SKILL.md`) — Web search via Tavily AI Search API for research, fact-checking, or content gathering.

## Reference docs

- `.kilo/reference/typst-troubleshooting.md` — Catalogue of Typst bugs encountered and fixes applied (page geometry, context blocks, pad-to-four, mode rules). **Consult before modifying any Typst layout code.**

## Environment variables

| Variable | Purpose | Set? |
|----------|---------|------|
| `DEEPSEEK_API_KEY` | Correction & summary via deepseek-v4-flash (DeepSeek API direct) | ✅ |
| `OPENROUTER_API_KEY` | Ingestion (OpenRouter) only | ✅ |
| `OPENAI_API_KEY` | (not used — kept for backward compatibility) | - |
| `CONTEXT7_API_KEY` | Context7 API key for library doc lookup (via `/context7` global skill) | ✅ |
| `TAVILY_API_KEY` | Tavily web search | ✅ |
| `SUPABASE_URL` | Supabase project URL | as needed |
| `SUPABASE_ESL_KEY` | Supabase service role key | as needed |
| `SUPABASE_ACCESS_TOKEN` | Personal Access Token for Management API (DDL / migrations) | Generate at supabase.com/dashboard/account/tokens |
| `SUPABASE_DB_URL` | (DEPRECATED) Direct Postgres connection string — use Management API instead | - |

## Models (current)

| Role | Model | Provider | Cost/M in | Cost/M out |
|------|-------|----------|-----------|------------|
| Correction | `deepseek-v4-flash` | DeepSeek API | $0.14 | $0.28 |
| Summary | `deepseek-v4-flash` | DeepSeek API | $0.14 | $0.28 |
| Ingestion | `google/gemini-2.5-flash` | OpenRouter | $0.10 | $0.40 |

Correction runs at temperature 0.6 (non-thinking mode). Summary runs at 0.8 (non-thinking mode). Full pipeline cost: ~$0.001 per student ($0.00085 ingest + $0.00006 correction + $0.00006 summary).

## Context7 documentation lookup

Context7 (`CONTEXT7_API_KEY`) indexes library documentation from GitHub repos, websites, npm packages, OpenAPI specs, and llms.txt sources. Use the **`/context7`** slash command (global skill) to query it:

```
/context7 — search Context7 by library name + specific question → returns code snippets and docs
```

Loads the global skill at `C:\Users\elwru\.kilo\skills\context7-docs/SKILL.md`. Falls back to Tavily → web fetch → GitHub API when a library is not indexed.

## Typst research methodology

Context7 has Typst indexed (ID: `/typst/typst`). Use Context7 as the first choice for Typst docs. The tiered approach below serves as fallback when Context7 returns insufficient results:

| Need | Tool | Example |
|------|------|---------|
| Official API reference | **Web fetch** from `typst.app/docs` | `webfetch("https://typst.app/docs/reference/layout/page/")` |
| Community patterns & solutions | **Tavily web search** | `tavily search "Typst pad to multiple of 4 pages pagebreak"` |
| Source-level docs | **`gh api`** on `typst/typst` repo | `gh api repos/typst/typst/contents/docs/...` |
| Changelog / version diffs | **`gh api`** changelog | `docs/content/changelog/` |
| Typst bugs & fixes (catalogued) | **Local reference** | `.kilo/reference/typst-troubleshooting.md` |

## Python project

| Item | Path |
|------|------|
| Main script | `src/ingest.py`, `src/errant_analysis.py`, `src/batch_errant_upsert.py`, `src/migrate_writing_records.py`, `src/rename_json_files.py`, `src/add_word_count.py`, `src/generate_report.py`, `src/interpret_results.py`, `src/desk_statistics.py`, `src/preflight_check.py`, `src/research_prep.py`, `src/sampling_strategy.py` |
| Tests | `tests/test_ingest.py`, `tests/test_errant.py`, `tests/test_rename_json_files.py`, `tests/test_report.py` |
| Dependencies | `requirements.txt` |
| Linter | `ruff` (config: `.ruff.toml`) |
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

## Pipeline

The full ERRANT analysis pipeline consists of these ordered stages. Each stage must complete before the next begins.

| # | Stage | Command | Script | Entry gate | Output | Exit gate |
|---|-------|---------|--------|------------|--------|-----------|
| 0 | Sampling plan | *(manual)* | `sampling_strategy.py` | — | `local-working/sampling_plan.json` | Plan approved |
| 1 | Ingestion | `/ingest-images` | `src/ingest.py` | Images in `inputs/{folder}/` | `outputs/{folder}/{student_id}.json` | Preflight check pass + human sign-off on image→ID mapping |
| 2a | ERRANT analysis (interactive) | `/errant-analysis` | `src/errant_analysis.py` | Ingestion outputs exist + sign-off confirmed | `local-working/{folder}-{record_id}.json` | All files processed |
| 2b | ERRANT batch upsert (Supabase) | *(manual)* | `src/migrate_writing_records.py` → `src/batch_errant_upsert.py` | Existing records in `error_reports` with NULL `error_percent` | Upserted error counts in Supabase | All records have `error_percent` populated |
| 3 | Rename JSONs | `/rename-json-files` | `src/rename_json_files.py` | ERRANT outputs exist | `local-working/{student_id}.json` | All names validated against Supabase classlist |
| 4 | Report generation | `/local-report` | `src/generate_report.py` | Renamed JSONs exist | PDF booklet(s) | Typst compiles without convergence warnings |
| 5 | Backup (optional) | `/git-backup` | *(git workflow)* | Changes to commit | Pushed to remote | — |

**Stage gates (blocking conditions):**
- **Preflight check:** After ingestion, run `src/preflight_check.py "FOLDER_NAME"` to detect artificial line breaks. If warnings appear, fix before proceeding.
- **ID sign-off (MANDATORY):** Present the image→ID mapping to the human. Do NOT proceed to ERRANT analysis without explicit confirmation.
- **Typst verification:** After report generation, verify the PDF compiles without "layout did not converge" warnings.

## Data lineage and class-label convention

**Class-label convention (critical — DO NOT misinterpret):**
The `class` field in ERRANT output JSONs uses M2/M3 as **enrollment status, not academic level:**
- **M2** = student_id is in the current `classlists` Supabase table (active, still enrolled)
- **M3** = student_id is NOT in `classlists` (left the program)

All 36 active ("M2") students are from academic levels M3-4A and M3-5A in the Supabase classlist. The label reflects enrollment, not which year they're in.

The Supabase `error_reports` table contains **986 records** across **141+ unique students**. The `class` column uses actual academic class labels (e.g. M2-4A, M3-3A, M3-4A, M3-5A) for the pre-batch pipeline records, and enrollment-status labels (M2, M3) for records from the batch upsert pipeline.

**CEFR level mapping for chart target lines:** All M3-M6 classes are B2 (target 7% error rate). Lower classes fall to B1 (target 12%).

## Input/output conventions

- Images: `inputs/{folder}/` — any JPEG or PNG filename accepted
- Ingestion output: `outputs/{folder}/{student_id}.json` with keys `student_id` and `student_text`
- Research prep output: `outputs/research/{record_id}.json` with per-record metadata (one file per student writing submission)
- ERRANT output: `local-working/{folder}-{record_id}.json` with full error analysis, sentence pairs, Typst-native `corrected_typst` field, metadata, and record metadata
- Multi-page essays combined into a single JSON, pages joined with a single space (never a newline)
- API key: `DEEPSEEK_API_KEY` in `.env` or environment; `OPENROUTER_API_KEY` for ingestion

## Transcription rules (enforced by prompt)

- Verbatim — retain ALL errors (grammar, spelling, vocabulary)
- Student ID extracted from ID field on the page (not filename)
- Transcribe ONLY handwriting on ruled lines — skip the demographic header block (ID, class, name fields)
- `\n` ONLY at paragraph boundaries; never at fixed character widths
- Crossed-out text skipped; carat/insertion symbols resolved to natural flow
