---
description: Run lint, tests, and quality review of uncommitted changes against project conventions
---

# Command: Review

Run all four phases in order. Stop and report at the first failure.

## Phase 1: Automated Checks

Run lint and tests. If either fails, report the failure and abort — do not proceed to quality review.

```bash
ruff check src/ tests/
pytest tests/ -v
```

## Phase 2: Uncommitted Changes Audit

Show what changed. If the working tree is clean, report and exit.

```bash
git status
git diff --stat
git diff
```

## Phase 3: Quality Review

Check every changed file against the rules below. List all violations with file paths and fix instructions.

### Python scripts (`src/*.py`)

1. **Secrets** — No hardcoded API keys or secrets. Keys loaded only via `os.environ` / `dotenv`.
2. **API URL** — Must be `https://api.openai.com/v1` (direct OpenAI, not OpenRouter).
3. **Model constants** — Must match documented values:
   - Ingestion: `google/gemini-2.5-flash-lite-preview-09-2025`
   - ERRANT correction: `gpt-4o-mini`
   - ERRANT summary: `gpt-4o-mini`
4. **Retry/backoff** — Exponential delay (`2^n` + jitter, capped 60s) on retries, max retries >= 3.
5. **Jitter** — Added to retry delays; not required between normal API calls.
6. **ERRANT temperatures** — Two correction passes at 0.1 and 0.5 (both must agree via edit-level majority voting).
7. **Transcription prompt** — Must enforce verbatim transcription (no corrections, `<br>` for breaks, skip crossed-out text, resolve carats to natural flow).
8. **Correction prompt** — Must enforce minimal change (grammar/spelling only, no rephrase, no style changes).
9. **`post_classify_other`** — Heuristic chain (aux verbs → R:VERB:TENSE, Levenshtein > 0.55 → R:SPELL, case-only → R:ORTH, shared prefix → R:MORPH, articles → R:DET, preps → R:PREP) must be preserved.
10. **Majority voting** — Both correction passes (temps 0.1, 0.5) must exist; edit intersection with `VOTE_THRESHOLD=2` must be present.
11. **Imports** — Every non-stdlib import must exist in `requirements.txt`.
12. **No dangerous patterns** — No `eval()`, `exec()`, `subprocess` with `shell=True` unless explicitly justified.

### Test files (`tests/*.py`)

1. **Import pattern** — Must use `sys.path.insert` with relative path, not hardcoded absolute paths.
2. **Fixtures** — Referenced fixture files must exist on disk (`tests/fixtures/error_golden.json`).
3. **Coverage** — Must test documented features: ingestion grouping/parsing/preprocessing, ERRANT error type detection, post-classify, metadata, edit intersection.
4. **No secrets** — No hardcoded API keys in test code or fixtures.

### Output JSON (`outputs/*.json`, `local-working/*.json`)

1. **Ingestion schema** — Must have exactly `student_id` (string) and `student_text` keys.
2. **ERRANT schema** — Must have all keys per errant-analysis SKILL.md schema: `student_id`, `original_text`, `corrected_text`, `sentence_pairs`, `errant_analysis`, `corrected_typst`, `error_rate`, `metadata`.
3. **Paragraph breaks** — `student_text` uses `\n`, not `<br>` or raw `\n\n`.
4. **No model leakage** — No raw markdown fences or model commentary in output fields.

### Configuration

1. **`.env`** — Must not be in staged or untracked files (excluded by `.gitignore`).
2. **`.ruff.toml`** — Per-file ignores must be scoped (e.g., only `tests/**`), not blanket disables.
3. **`requirements.txt`** — Must list every non-stdlib import used in `src/` and `tests/`.

### Documentation

1. **AGENTS.md slash commands** — Must match `.kilo/command/` files (one entry per command).
2. **AGENTS.md skills** — Must match `.kilo/skills/` directories (one entry per skill).
3. **Skill accuracy** — Skill files must not reference removed or nonexistent features (e.g., prompt caching, Qwen3 model).
4. **ERRANT no-guess rule** — `errant-analysis/SKILL.md` must contain the "do not guess ERRANT internals" directive with `gh api` commands.

## Phase 4: Report

Output a summary in this format:

```
=== REVIEW REPORT ===

--- Phase 1: Automated Checks ---
Lint:  PASSED/FAILED
Tests: PASSED/FAILED (N/N)

--- Phase 2: Changed Files ---
<list of changed files>

--- Phase 3: Quality Violations ---
<file>: <rule reference> — <fix instruction>
-or-
NONE — all rules pass

=== CONCLUSION ===
PASSED / FAILED — <next steps>
```

If violations exist, present them as actionable instructions so the agent can fix them before proceeding.
