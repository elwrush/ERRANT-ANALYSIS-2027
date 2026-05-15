# Skill: supabase-classlist

## Purpose

For a new academic year: **delete all existing records** from the Supabase `classlists` table, then **insert fresh records** from `docs/students.txt` using `supabase` (supabase-py). This replaces the previous upsert approach — no merging, no class transfers, just a clean slate.

## Files

| Item | Path |
|------|------|
| Script | `src/supabase_classlist.py` |
| Tests | `tests/test_supabase_classlist.py` |
| Source data | `docs/students.txt` |

## Prerequisites

```bash
pip install -r requirements.txt
```

Set environment variables (available in Windows environment):

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ESL_KEY` | Service role key (`sb_secret_...`) for write access |

## Input

`docs/students.txt` — tab-separated, 4 columns: Class, student_ID, name, trailing. Example:
```
Class	student_ID	 name
M2-4A	36018	Pooh	0
M2-4A	30399	Mick	0
```

The trailing column is ignored. Only the first 3 columns are used.

## Table Schema

```sql
create table public.classlists (
  student_id text not null,
  name text not null,
  class text not null,
  created_at timestamp with time zone not null default timezone ('Asia/Bangkok'::text, now()),
  updated_at timestamp with time zone not null default timezone ('Asia/Bangkok'::text, now()),
  user_id uuid null default auth.uid (),
  constraint classlists_pkey primary key (student_id),
  constraint classlists_user_id_fkey foreign key (user_id) references auth.users (id)
);
```

## Usage

### Sync all students (delete + insert)

```bash
python src/supabase_classlist.py
```

1. Reads `docs/students.txt` (93 students across 5 classes)
2. Deletes ALL existing records from `classlists`
3. Inserts every row from the text file fresh
4. Reports counts of deleted, inserted, and errored rows

### Check a single student

```bash
python src/supabase_classlist.py --check 36018
```

Returns exit code 0 if the student_id exists in the classlist, 1 if not. This mode is used by the rename-json-files workflow.

## Edge cases

| Scenario | Behavior |
|----------|----------|
| Missing env vars | Error message, exit code 1 |
| Empty file | Deletes all, inserts nothing |
| Missing `student_id` | Skips row with warning during insert |
| Network error during delete | Reports 0 deleted, continues to insert |
| Network error during insert | Reports error per row, continues processing |
| Duplicate student_id in source | Last duplicate wins (PK constraint) |
| Trailing column | Ignored |
