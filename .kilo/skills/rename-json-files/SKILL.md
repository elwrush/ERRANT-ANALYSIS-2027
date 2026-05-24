# Skill: rename-json-files

## Purpose

Rename ERRANT output JSONs in `local-working/` from prefixed names (`M2-4A-36018.json`) to plain student ID names (`36018.json`), validated against Supabase classlist.

## Usage

```bash
python src/rename_json_files.py
```

The script scans all JSONs in `local-working/`, extracts `student_id` from content, validates against Supabase classlists table, and renames valid files to `{student_id}.json`. Missing students are reported for manual handling.

## Prerequisites

`SUPABASE_URL` and `SUPABASE_ESL_KEY` env vars (optional — skips validation if missing).
