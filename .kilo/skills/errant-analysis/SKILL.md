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
- `date_created` — ISO date (YYYY-MM-DD) of when the ERRANT analysis was run; written to the `date` column in the `error_reports` Supabase table on upload

## Supabase interactions

This project uses Supabase for:
1. **Classlist lookup** — `classlists` table (read via postgrest client)
2. **Writing error reports** — `error_reports` table (insert via postgrest client)  
3. **Historical data** — `error_reports` (read via postgrest client)
4. **DDL / migrations** — `supabase_sql.py` utility (via Management API)

### Environment variables

| Variable | Purpose | How to get |
|----------|---------|------------|
| `SUPABASE_URL` | PostgREST endpoint | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_ESL_KEY` | Service role key (anon key also works for reads) | Supabase Dashboard → Settings → API → `service_role` key |
| `SUPABASE_ACCESS_TOKEN` | Management API token for DDL / migrations | https://supabase.com/dashboard/account/tokens → Generate token → `sbp_...` |

### SQL migrations (DDL)

Do NOT use `psycopg2` or direct DB connection strings. Use the `supabase_sql.py` utility:

```bash
# Single query
python src/supabase_sql.py "ALTER TABLE error_reports ADD COLUMN IF NOT EXISTS date DATE;"

# From a SQL file
python src/supabase_sql.py -f src/setup_error_analysis.py

# Force raw API mode (skip CLI)
python src/supabase_sql.py --api "SELECT COUNT(*) FROM error_reports;"
```

The utility auto-detects two modes:
1. **supabase CLI** (`supabase db query --linked`) — preferred, handles output formatting
2. **Management API** (`POST /v1/projects/{ref}/database/query`) — fallback

The project must be linked:
```bash
supabase link --project-ref <ref>
```

The project ref is visible in your Supabase Dashboard URL: `https://supabase.com/dashboard/project/hdpwaqprrgnndkgzmnan`.

The linked-project info is stored in `supabase/.temp/linked-project.json`.

### Runtime inserts (error_reports)

The `insert_error_reports()` function in `errant_analysis.py` uses the **postgrest client** (Supabase Python SDK) with `SUPABASE_URL` + `SUPABASE_ESL_KEY`. This is the correct approach for row-level inserts — the Management API is for DDL only.

### Maintaining the migration script (`setup_error_analysis.py`)

`setup_error_analysis.py` defines all ERROR_CODE_COLUMNS (45 error-type columns) plus `date` and `academic_year`. It runs via `supabase_sql.py`:

```bash
python src/setup_error_analysis.py
```

When adding new columns, just add them to `NEW_COLUMNS` or `COLUMNS_SQL` lists — no psycopg2 needed.

### Quick reference: running queries

```bash
# Count rows
supabase db query --linked "SELECT COUNT(*) FROM error_reports;"

# Check date column
supabase db query --linked "SELECT student_id, date FROM error_reports LIMIT 5;"

# Via utility
python src/supabase_sql.py "SELECT * FROM error_reports LIMIT 3;"
```

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Required env vars:
- `DEEPSEEK_API_KEY` — correction & summary via deepseek-v4-flash (DeepSeek API direct)
- `SUPABASE_URL` + `SUPABASE_ESL_KEY` — for classlist lookup and Supabase upload (skipped if absent)

Optional but recommended:
- `SUPABASE_ACCESS_TOKEN` — for schema migrations via Management API
- `supabase` CLI — for ad-hoc queries and formatted output
