# AGENTS.md

## Project: ERRANT-ANALYSIS

Pipelines student handwriting images through OCR transcription (Gemini via OpenRouter), ERRANT grammatical error analysis, Supabase storage, and report generation.

## Shell: Windows PowerShell 5.1

This project runs on Windows PowerShell 5.1. See `.kilo/agent/powershell.md` for shell-specific syntax requirements — use this as a reference when writing or troubleshooting commands.

## Slash commands

- `/ingest-papers` — Transcribe handwritten essays from `inputs/` subfolders using `google/gemini-2.5-flash-lite-preview-09-2025`
- `/local-errant-analysis` — Run ERRANT grammatical error analysis on transcribed essays
- `/git-backup` — Diff, commit with a verbose message, and push to remote
- `/supabase-classlist` — Sync `docs/students.txt` classlist data to Supabase
- `/rename-json-files` — Rename ERRANT output JSONs to student_id.json, validated against Supabase classlist
- `/review` — Run lint, tests, and quality review of uncommitted changes against project conventions
- `/local-report` — Generate Typst report booklets from ERRANT analysis with summary, charts, and PDF output

## Skills

- `.kilo/skills/ingest-images/SKILL.md` — Full workflow for handwriting image ingestion and transcription
- `.kilo/skills/errant-analysis/SKILL.md` — Full workflow for grammatical error analysis with ERRANT
- `.kilo/skills/git-backup/SKILL.md` — Full workflow for diff, commit, and push
- `.kilo/skills/supabase-classlist/SKILL.md` — Full workflow for Supabase classlist management via supabase-py
- `.kilo/skills/rename-json-files/SKILL.md` — Full workflow for renaming ERRANT output files with classlist validation
- `.kilo/skills/local-report/SKILL.md` — Full workflow for generating Typst report booklets with summary, charts, and PDF compilation
- `.kilo/skills/tavily-websearch/SKILL.md` — Global skill: Web search via Tavily AI Search API (5 pre-written Python models). Use for research, fact-checking, or content gathering. Copy the script verbatim from the skill, change only the query/URL/parameters.

## Reference docs

- `.kilo/reference/typst-troubleshooting.md` — Catalogue of Typst bugs encountered and fixes applied (page geometry, context blocks, pad-to-four, mode rules). **Consult before modifying any Typst layout code.**

## Environment variables

| Variable | Purpose | Set? |
|----------|---------|------|
| `OPENROUTER_API_KEY` | LLM API for corrections & summaries | ✅ |
| `CONTEXT7_API_KEY` | Context7 MCP for library doc retrieval (see Typst research below) | ✅ |
| `TAVILY_API_KEY` | Tavily web search | ✅ |
| `SUPABASE_URL` | Supabase project URL | as needed |
| `SUPABASE_ESL_KEY` | Supabase service role key | as needed |

## Models (current)

| Role | Model | Cost/M in | Cost/M out |
|------|-------|-----------|------------|
| Correction | `google/gemma-4-31b-it` | $0.12 | $0.37 |
| Summary | `google/gemma-4-31b-it` | $0.12 | $0.37 |
| Ingestion | `google/gemini-2.5-flash-lite-preview-09-2025` | | |

Correction runs at two temperatures (0.1 and 0.3) with double-check intersection. Summary runs at 0.8. Both use OpenRouter. Full pipeline cost: ~$0.00042 per student.

## Typst research methodology

Context7 (`CONTEXT7_API_KEY`) is an MCP server for library documentation — **Typst is NOT indexed** (returns 404). Use this tiered approach instead:

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
| Main script | `src/ingest.py`, `src/errant_analysis.py`, `src/supabase_classlist.py`, `src/rename_json_files.py`, `src/add_word_count.py`, `src/generate_report.py` |
| Tests | `tests/test_ingest.py`, `tests/test_errant.py`, `tests/test_supabase_classlist.py`, `tests/test_rename_json_files.py`, `tests/test_report.py` |
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

## Input/output conventions

- Images: `inputs/{folder}/` — any JPEG or PNG filename accepted
- Ingestion output: `outputs/{folder}/{student_id}.json` with keys `student_id` and `student_text`
- ERRANT output: `local-working/{folder}-{student_id}.json` with full error analysis, sentence pairs, Typst-native `corrected_typst` field, and metadata
- Multi-page essays combined into a single JSON, pages joined with `\n`
- API key: `OPENROUTER_API_KEY` in `.env` or environment

## Transcription rules (enforced by prompt)

- Verbatim — retain ALL errors (grammar, spelling, vocabulary)
- Student ID extracted from ID field on the page (not filename)
- `\n` ONLY at paragraph boundaries; never at fixed character widths
- Crossed-out text skipped; carat/insertion symbols resolved to natural flow
