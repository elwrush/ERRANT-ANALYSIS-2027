# AGENTS.md

## Project: ERRANT-ANALYSIS

Full ERRANT analysis pipeline: ingests student handwriting images via OCR transcription (Gemini via OpenRouter), runs grammatical error analysis with DeepSeek V4 Flash + ERRANT, uploads structured reports to Supabase, and generates Typst report booklets with PDF output.

## Shell: Windows PowerShell 5.1

This project runs on Windows PowerShell 5.1.

## Slash commands

- `/ingest-papers` — Transcribe handwritten essays from `inputs/` subfolders using `google/gemini-2.5-flash-lite-preview-09-2025`
- `/local-errant-analysis` — Run ERRANT grammatical error analysis on transcribed essays
- `/git-backup` — Diff, commit with a verbose message, and push to remote
- `/rename-json-files` — Rename ERRANT output JSONs to student_id.json, validated against Supabase classlist
- `/review` — Run lint, tests, and quality review of uncommitted changes against project conventions
- `/local-report` — Generate Typst report booklets from ERRANT analysis with summary, charts, and PDF output
- `/context7` — Search Context7 for up-to-date library documentation (global skill)

## Skills

- `.kilo/skills/ingest-images/SKILL.md` — Full workflow for handwriting image ingestion and transcription
- `.kilo/skills/errant-analysis/SKILL.md` — Full workflow for grammatical error analysis with ERRANT
- `.kilo/skills/git-backup/SKILL.md` — Full workflow for diff, commit, and push
- `.kilo/skills/rename-json-files/SKILL.md` — Full workflow for renaming ERRANT output files with classlist validation
- `.kilo/skills/local-report/SKILL.md` — Full workflow for generating Typst report booklets with summary, charts, and PDF compilation
- `.kilo/skills/tavily-websearch/SKILL.md` — Global skill: Web search via Tavily AI Search API (5 pre-written Python models). Use for research, fact-checking, or content gathering. Copy the script verbatim from the skill, change only the query/URL/parameters.
- `.kilo/skills/context7-docs/SKILL.md` — Global skill: Query library documentation via Context7 REST API (3 pre-written Python models). Use for checking if documentation exists for a library, then fetching version-specific code examples and API references. Falls back to Tavily when a library is not indexed.

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

## Models (current)

| Role | Model | Provider | Cost/M in | Cost/M out |
|------|-------|----------|-----------|------------|
| Correction | `deepseek-v4-flash` | DeepSeek API | $0.14 | $0.28 |
| Summary | `deepseek-v4-flash` | DeepSeek API | $0.14 | $0.28 |
| Ingestion | `google/gemini-2.5-flash-lite-preview-09-2025` | OpenRouter | | |

Correction runs at temperature 0.1 (minimal edits). Summary runs at 0.8 (non-thinking mode). Full pipeline cost: ~$0.00039 per student.

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
| Main script | `src/ingest.py`, `src/errant_analysis.py`, `src/rename_json_files.py`, `src/add_word_count.py`, `src/generate_report.py`, `src/interpret_results.py`, `src/desk_statistics.py` |
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

## Data lineage and class-label convention

- Source table: `student_submissions` in Supabase (filter: skill='Writing') (each row = one essay submission)
- Sampling plan: `sampling_strategy.py` → `local-working/sampling_plan.json`
- Research prep: `research_prep.py` → `outputs/research/{record_id}.json`
- Ingestion: `ingest.py` → `outputs/{folder}/{student_id}.json`
- **ID verification (MANDATORY sign-off):** After ingestion, the agent must present the image→ID mapping to the human for confirmation. Only after sign-off does the pipeline proceed.
- ERRANT analysis: `errant_analysis.py` → `local-working/{folder}-{record_id}.json`

**Class-label convention (critical — DO NOT misinterpret):**
The `class` field in ERRANT output JSONs uses M2/M3 as **enrollment status, not academic level:**
- **M2** = student_id is in the current `classlists` Supabase table (active, still enrolled)
- **M3** = student_id is NOT in `classlists` (left the program)

All 36 active ("M2") students are from academic levels M3-4A and M3-5A in the Supabase classlist. The label reflects enrollment, not which year they're in. This is consistent across all 689 files (zero anomalies).

## Input/output conventions

- Images: `inputs/{folder}/` — any JPEG or PNG filename accepted
- Ingestion output: `outputs/{folder}/{student_id}.json` with keys `student_id` and `student_text`
- Research prep output: `outputs/research/{record_id}.json` with per-record metadata (one file per student writing submission)
- ERRANT output: `local-working/{folder}-{record_id}.json` with full error analysis, sentence pairs, Typst-native `corrected_typst` field, metadata, and record metadata
- Multi-page essays combined into a single JSON, pages joined with `\n`
- API key: `DEEPSEEK_API_KEY` in `.env` or environment; `OPENROUTER_API_KEY` for ingestion

## Transcription rules (enforced by prompt)

- Verbatim — retain ALL errors (grammar, spelling, vocabulary)
- Student ID extracted from ID field on the page (not filename)
- `\n` ONLY at paragraph boundaries; never at fixed character widths
- Crossed-out text skipped; carat/insertion symbols resolved to natural flow
