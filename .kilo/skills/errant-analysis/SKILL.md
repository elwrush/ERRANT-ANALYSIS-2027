# Skill: errant-analysis

## Purpose

Takes transcribed student essays (`outputs/{folder}/{student_id}.json`), runs sentence-by-sentence correction via DeepSeek V4 Flash (deepseek-v4-flash), compares original vs corrected with ERRANT for structured error classification, generates personalised AI summaries via DeepSeek V4 Flash (non-thinking mode), and saves results to `local-working/`.

## Usage

### Interactive mode (human at terminal)
```bash
python src/errant_analysis.py
```
Shows a numbered menu of available files from `outputs/`. Select one to process.

### Batch mode (for agents / automation)
```bash
python src/errant_analysis.py --batch "M2-5A BASELINE"
```
Processes all JSON files in `outputs/` with 5 parallel workers. Optional folder filter after `--batch` limits to a specific subfolder.

### Agent workflow

**Prerequisite:** Ingestion outputs must have their student IDs verified by the human (see `ingest-images` skill — "ID verification sign-off" section). Do not proceed if IDs haven't been confirmed.

Use the `question` tool to ask the user which folder to process, then run:
```bash
python src/errant_analysis.py --batch "FOLDER_NAME"
```

## Output

One JSON file per student, saved to `local-working/` with the naming pattern:

```
local-working/{folder}-{student_id}.json
```

For example, `outputs/M2-4A BASELINE/30399.json` produces `local-working/M2-4A BASELINE-30399.json`.

Each output file contains:
- `original_text`, `corrected_text`, `corrected_typst` (with `#underline[correction]` markup)
- `errant_analysis.errors[]` — error types with counts and context spans
- `sentence_pairs[]` — aligned original/corrected sentence pairs
- `summary` — personalised feedback with hallucination-verified examples
- `summary_type` — `"llm"` or `"local"` (flagged files needing probabilistic rewrite)
- `error_rate` — `total_edit_count / word_count × 100`
- `name`, `class` — from the input JSON or Supabase classlist lookup

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Required env vars:
- `DEEPSEEK_API_KEY` — correction & summary via deepseek-v4-flash (DeepSeek API direct)

Optional:
- `SUPABASE_URL` + `SUPABASE_ESL_KEY` — for classlist lookup and Supabase upload (skipped if absent)
