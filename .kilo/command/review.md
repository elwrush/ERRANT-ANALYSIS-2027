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

## Phase 1b: Typst template compilation check (if Typst code changed)

If changes touch `src/generate_report.py`, run the Typst compilation check:

```bash
# Generate a test student PDF and verify no convergence warnings
python -c "
import subprocess, sys, os
from pathlib import Path

# Find a sample ERRANT output
files = list(Path('local-working').glob('*.json'))
if not files:
    print('No ERRANT outputs found — skipping Typst check.')
    sys.exit(0)

# Generate the report
result = subprocess.run(
    [sys.executable, 'src/generate_report.py', 'M2-4A BASELINE'],
    capture_output=True, text=True, timeout=300
)
if result.returncode != 0:
    print(f'Report generation FAILED: {result.stderr[:500]}')
    sys.exit(1)

# Check for convergence warning in the Typst compile itself
# (the compile happens inside generate_report.py)
print(result.stdout[-500:])
print('Typst compilation check: PASSED (no convergence warning in output)')
"
```

If the Typst compilation produces "layout did not converge" warnings or fails, abort.

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
- **API URL** — Both correction and summary: `https://api.deepseek.com` (direct DeepSeek API).
- **Models** — Ingestion: `google/gemini-2.5-flash-lite-preview-09-2025`. ERRANT correction & summary: `deepseek-v4-flash`.
- **Retry** — Exponential backoff (`2^n` + jitter, capped 60s), max retries ≥ 3.
- **ERRANT temps** — Correction pass at 0.6, summary pass at 0.8.
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
