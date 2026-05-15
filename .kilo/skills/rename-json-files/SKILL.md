# Skill: rename-json-files

## Purpose

After ERRANT analysis completes, rename the output JSON files in `local-working/` from their folder-prefixed names (e.g. `M2-4A-36018.json`) to plain student ID names (`36018.json`). Each file is validated against the Supabase classlist before renaming. Files with student IDs not found in the classlist are reported to the user for manual handling.

## Files

| Item | Path |
|------|------|
| Script | `src/rename_json_files.py` |
| Tests | `tests/test_rename_json_files.py` |

## Prerequisites

```bash
pip install -r requirements.txt
```

Set environment variables (optional — falls back to unvalidated rename):

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ESL_KEY` | Service role key (`sb_secret_...`) |

If Supabase credentials are not available, the script still renames files but skips classlist validation.

## Usage

```bash
python src/rename_json_files.py
```

The script:
1. Scans all JSON files in `local-working/`
2. For each file, extracts the `student_id` from JSON content
3. Checks if the student_id exists in the Supabase classlist
4. If found: renames to `{student_id}.json` (e.g. `36018.json`)
5. If not found: alerts the user and skips the file
6. Reports counts of renamed and skipped files

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No JSON files | Reports message, exits cleanly |
| No Supabase credentials | Renames without validation, warns user |
| Duplicate student_id across files | Renames first, skips subsequent with warning |
| Malformed JSON | Skips with alert |
| Missing `student_id` key | Skips with alert |
| Student not in classlist | Skips with alert, user renames manually |
| Supabase unreachable | Treats as validation failure, skips rename |
