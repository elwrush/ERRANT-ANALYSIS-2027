# Skill: errant-analysis

## Purpose

Takes transcribed student essays (`outputs/{folder}/{student_id}.json`), runs sentence-by-sentence correction via OpenAI, compares original vs corrected with ERRANT for structured error classification, generates personalized AI summaries, and saves results to `local-working/`.

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
Use the `question` tool to ask the user which folder to process, then run:
```bash
python src/errant_analysis.py --batch "FOLDER_NAME"
```

## Output

Saved to `local-working/{folder}-{record_id}.json` with:
- `original_text`, `corrected_text`, `corrected_typst` (with `#underline[correction]` markup)
- `errant_analysis.errors[]` — error types with counts and context spans
- `sentence_pairs[]` — aligned original/corrected sentence pairs
- `summary` — personalised feedback with hallucination-verified examples
- `error_rate` — `total_edit_count / word_count × 100`
- `name`, `class` — from the input JSON or Supabase classlist lookup

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Required env vars: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ESL_KEY`.
