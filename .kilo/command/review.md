---
description: Run lint, tests, and quality review of uncommitted changes against project conventions
---

Run all four phases below. Stop on first failure.

## Phase 1: Automated Checks

```bash
ruff check src/ tests/
pytest tests/ -v
```

If either fails, report and abort.

## Phase 2: Uncommitted Changes

```bash
git status
git diff --stat
git diff
```

If working tree is clean, report and exit.

## Phase 3: Quality Review

Check every changed file against these rules. List all violations with file paths.

- **Secrets** — No hardcoded API keys. Keys via `os.environ`/`dotenv` only.
- **API URL** — Must be `https://api.openai.com/v1` (direct OpenAI).
- **Models** — Ingestion: `google/gemini-2.5-flash-lite-preview-09-2025`. ERRANT correction: `gpt-4.1-nano`. Summary: `gpt-4o-mini`.
- **Retry** — Exponential backoff (`2^n` + jitter, capped 60s), max retries ≥ 3.
- **ERRANT temps** — Two correction passes at 0.1 and 0.5 with edit-level majority voting.
- **Imports** — Every non-stdlib import must be in `requirements.txt`.
- **No dangerous patterns** — No `eval()`, `exec()`, `subprocess` with `shell=True`.
- **Test import pattern** — Uses `sys.path.insert` relative path, not hardcoded absolute.
- **`post_classify_other`** — Heuristic chain must be preserved.
- **Output schemas** — Ingestion: `student_id` + `student_text` + `name` + `class` + `source_images`. ERRANT: all keys per schema.
- **`.env`** — Must not be staged (excluded by `.gitignore`).
- **Skill accuracy** — No references to removed features (e.g. `students.txt`, `supabase_classlist.py`).

## Phase 4: Report

```
=== REVIEW REPORT ===
Phase 1: Lint PASSED/FAILED | Tests PASSED/FAILED (N/N)
Phase 2: <changed files>
Phase 3: NONE / <violations>
=== PASSED / FAILED ===
```
