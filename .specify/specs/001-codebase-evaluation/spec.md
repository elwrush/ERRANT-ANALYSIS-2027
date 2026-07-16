# Codebase Evaluation and Refactoring Assessment

## Feature Summary

Evaluate the full ERRANT analysis pipeline codebase for technical debt, architecture integrity, and maintainability. Produce a prioritized roadmap: targeted micro-refactors vs. full pipeline rewrite.

---

## User Stories

| Priority | Story |
|----------|-------|
| P1 | As a developer, I want a clear dependency graph of all 21 source scripts so I understand the module coupling and can plan refactors safely. |
| P1 | As a maintainer, I want the two PDF generation paths (legacy Typst vs. new Jinja2/Playwright) consolidated so there is one source of truth for report output. |
| P1 | As a pipeline operator, I want all scripts to use a shared configuration module so environment variables, paths, and constants are not duplicated across 21 files. |
| P2 | As a developer, I want `response_format={"type": "json_object"}` enforced on all LLM calls so malformed JSON is structurally impossible. |
| P2 | As a developer, I want Pydantic model validation on all JSON write paths so schema drift is caught before data reaches downstream consumers. |
| P2 | As a tester, I want the 4 existing test files expanded to cover all 21 source modules so regressions are caught during refactoring. |
| P3 | As a developer, I want the `_retry.py` decorator unified with the per-module retry logic in `errant_analysis.py` so there is one retry strategy. |
| P3 | As a maintainer, I want unused or one-shot scripts (pilot_prep.py, query_class_mapping.py, query_skill_count.py, write_historical_data.py) archived so the src/ directory only contains actively used pipeline scripts. |

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | The dependency graph must be machine-generated (e.g., `pydeps` or static import scanning) and identify circular dependencies. |
| FR-002 | The Typst compilation path in `generate_report.py` (lines 600-603) must be replaced with a Jinja2→Playwright→PDF pipeline that produces **pixel-equivalent** output (layout, masthead, logos, chart positions, 4-page padding). |
| FR-003 | All shared constants (API keys, model names, paths, error code mappings) must live in a single `config.py` or `.env`-backed settings module, not inline in each script. |
| FR-004 | ERRANT code-to-column mappings (`ERRANT_CODE_TO_COLUMN`) must be defined in one canonical location — currently duplicated in `errant_analysis.py` and `generate_report.py`. |
| FR-005 | Every LLM API call must use `response_format={"type": "json_object"}` — currently 0 of 3 LLM call sites use it (ingest.py, errant_analysis.py correction and summary). |
| FR-006 | Every JSON write to disk must validate through `BaseModel.model_validate()` — currently 0 of 21 scripts use Pydantic validation. All models must live in a single `src/models.py` file. |
| FR-007 | All 21 source modules must have a corresponding test file in tests/ with smoke tests (import + key function signatures) plus unit tests achieving >60% line coverage on core modules (`errant_analysis.py`, `ingest.py`, `generate_report.py`). Each unit test must assert a specific behavioural outcome (return value, side effect, or raised exception) — not merely verify import success. |
| FR-008 | The following one-shot scripts must be moved to `scripts/archive/` with a README documenting their purpose and last-use date (from `git log -1 --format=%ai <file>`): `pilot_prep.py`, `query_class_mapping.py`, `query_skill_count.py`, `write_historical_data.py`, `test_models.py`, `add_word_count.py`. |

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Dependency graph identifies max 2 levels of transitive import depth | Generated graph shows no imports deeper than 3 levels |
| Playwright PDF renders correctly with all sections | Visual inspection confirms masthead, chart, corrected text, original text, summary, and date are present and well-formatted |
| Typst dependency removed from requirements.txt | `requirements.txt` contains no `typst` or pypdf reference |
| All LLM calls use response_format | grep for all `chat.completions.create` shows `response_format` on every call |
| All JSON writes use model_validate | grep for `json.dump` and `write_text` on `.json` files shows preceding `model_validate` call |
| No duplicated ERRANT code mappings | `ERRANT_CODE_TO_COLUMN` appears in exactly 1 file |
| All 21 modules have test coverage | `pytest --cov=src` reports >60% module coverage |
| One-shot scripts archived | `scripts/archive/` contains at most the identified one-shot scripts with README |
| Pipeline runs end-to-end without Typst | `python src/generate_report.py` produces PDF via Playwright without calling `typst compile` |
| Playwright PDF renders all sections correctly | Visual inspection confirms masthead, chart, corrected markup, original text, summary, and signature present with correct layout |

---

## Edge Cases

| Case | Expected handling |
|------|-------------------|
| Playwright not installed | Graceful fallback with error message: "Install playwright: pip install playwright && playwright install chromium" |
| Existing .typ files in outputs/ | Archive or skip with warning, do not delete user data |
| Supabase unavailable during refactored pipeline | Pipeline degrades gracefully (skip upsert, log warning) as current code does |
| Jinja2 template missing | Clear error: "Template not found at templates/report.html" |
| Mixed legacy Typst + new Playwright PDFs in same output directory | No filename collision — use distinct naming convention (e.g. `*_playwright.pdf`) |
| Pre-existing legacy JSON files (old schema before Pydantic migration) consumed by refactored code | Detect missing `word_count` or wrong `student_text` key; apply `model_validate(..., strict=False)` to coerce known shorthands; log a warning for each coerced field |

---

## Non-Functional Requirements

| ID | Requirement | Measurement |
|----|-------------|-------------|
| NFR-001 | Single-student PDF generation must complete within 10 seconds on a typical developer machine (8-core, 16 GB RAM, SSD) | `time python -c "from generate_report import ..."` reports <10s wall-clock for one student |
| NFR-002 | Batch PDF generation (36 students, single class) must complete within 10 minutes | `time python src/generate_report.py` reports <600s wall-clock |
| NFR-003 | Playwright Chromium headless must not consume more than 500 MB RSS per PDF generation | `psutil` or OS-level RSS measurement during `html_to_pdf()` |
| NFR-004 | All Pydantic model validations combined must add <100ms overhead per JSON write (vs raw json.dump) | `timeit` comparison of `model_validate` + `json.dump` vs bare `json.dump` |

---

## Key Entities

| Entity | Description |
|--------|-------------|
| Pipeline script (`src/*.py`) | Each of the 21 Python modules in the pipeline |
| LLM client wrapper | Unified abstraction over DeepSeek/OpenRouter API calls with response_format enforcement |
| Config module | Single settings source for paths, model names, API keys, error code mappings |
| Pydantic models | Validation schemas for ingestion output, ERRANT output, and report data |
| Test suite | `pytest` tests covering all source modules |
| Legacy Typst templates | `.typ` files and `build_typ_header()` / `build_student_block()` functions to be replaced |
| Jinja2/Playwright renderer | New PDF generation pipeline replacing Typst |

---

## Assumptions

| # | Assumption | Confidence |
|---|------------|------------|
| 1 | The ERRANT library (`errant>=3.0.0`) and spaCy (`en_core_web_sm`) are pinned in requirements.txt and available via pip. No version conflicts with Playwright or Python 3.14. | High |
| 2 | The Jinja2→Playwright→PDF pipeline must produce **pixel-equivalent** output to the current Typst output. A visual diff comparison is scoped to the refactor implementation. | High |
| 3 | The six identified one-shot scripts (`pilot_prep.py`, `query_class_mapping.py`, `query_skill_count.py`, `write_historical_data.py`, `test_models.py`, `add_word_count.py`) are safe to archive. | High |

---

## Clarifications (2026-07-13)

| # | Question | Resolution | Impact on Spec |
|---|----------|------------|----------------|
| 1 | Playwright visual fidelity vs. Typst | **Functional equivalent** — Playwright output must contain all sections (masthead, logos, chart, corrected text, original text, summary) rendered cleanly. Visual inspection, not pixel-diff against Typst (which is removed). | FR-002 scope updated: visual inspection replaces pixel-diff since Typst pipeline was removed per user instruction. |
| 2 | Which one-shot scripts to archive | **Archive all six** — `pilot_prep.py`, `query_class_mapping.py`, `query_skill_count.py`, `write_historical_data.py`, `test_models.py`, `add_word_count.py` → `scripts/archive/`. | FR-008 updated. Archive list finalized. |
| 3 | Python version target | **Python 3.14** — stable release. Verify all deps (errant, spaCy, playwright) have 3.14 wheels before proceeding. | All refactored code must be 3.14-compatible. |
| 4 | Pydantic model granularity | **Single `src/models.py`** — one canonical file for all pipeline data models (IngestionOutput, ErrantOutput, ReportData). | FR-006 scope: create `src/models.py` with BaseModel subclasses for each JSON shape. |
| 5 | Test depth | **Smoke tests (all modules) + >60% line coverage** on core modules. | FR-007 metric confirmed: smoke tests mandatory, coverage target 60%+. |

---

## Recommendations Summary

### Do NOT do a full refactor — recommend targeted micro-refactors

The codebase is structurally sound. Key arguments:

1. **No circular dependencies** — imports follow a clean DAG: utility scripts → `errant_analysis.py` (central hub) → `generate_report.py` (leaf). No cycles detected.
2. **Consistent patterns** — all scripts use the same `.env`→`os.environ.get()` pattern, same `Path` usage, same `sys.path.insert` test pattern. No architectural rot.
3. **Test coverage exists** — 4 test files with 50+ test cases. Not complete, but not zero.
4. **Single responsibility holds** — each script does one thing (ingest, correct, analyze, report, migrate, stats). No god modules.

### Highest-ROI improvements (in priority order)

| Priority | Change | Effort | Risk | Impact |
|----------|--------|--------|------|--------|
| 1 | Replace Typst pipeline with Jinja2→Playwright | 3-4 days | Medium | Eliminates fragile Typst compilation, convergence warnings, font issues |
| 2 | Add `response_format` to all LLM calls | 0.5 day | Low | Eliminates JSON parse failures from LLM output |
| 3 | Add Pydantic models for all JSON write paths | 1-2 days | Low | Catches schema drift before it reaches downstream consumers |
| 4 | Consolidate config into single `config.py` | 0.5 day | Low | Eliminates duplicated constants, env var lookups, path definitions |
| 5 | Expand test coverage to all 21 modules | 2-3 days | Low | Enables safe refactoring of any module |
| 6 | Archive one-shot scripts | 0.25 day | None | Keeps src/ lean, clarifies which scripts are actively used |

### Do NOT invest in

- Rewriting the LLM interaction layer — the OpenAI client abstraction is adequate
- Replacing the ThreadPoolExecutor pattern — it's correct for I/O-bound API calls
- Adding type hints — scripts run, no static type checker configured
- Containerization — the `.env`/`requirements.txt` pattern works for this team

### Assessment: Targeted micro-refactors will yield 90% of the benefit at 10% of the cost of a full rewrite.
