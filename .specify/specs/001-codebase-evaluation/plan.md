# Technical Implementation Plan — Codebase Evaluation & Refactoring

## Tech Stack

| Layer | Current | Target | Rationale |
|-------|---------|--------|-----------|
| **PDF generation** | Typst CLI (`subprocess.run(["typst", "compile"])`) | Jinja2 + Playwright Python | Eliminates fragile Typst compiler, font-path issues, convergence warnings. Pure Python end-to-end. |
| **Data validation** | None (raw `json.dump`/`json.load`) | Pydantic v2 (`BaseModel.model_validate()`) | Catch schema drift before it reaches downstream. Required by global compliance rules. |
| **LLM invocation** | Raw OpenAI client with `max_retries=0` | Same client + `response_format` enforcement | Eliminates JSON parse failures. Required by global compliance rules. |
| **Config management** | Inline constants per script | `src/config.py` with `.env` fallback | Single source of truth for paths, model names, API keys, error code mappings. |
| **Constants** | Duplicated `ERRANT_CODE_TO_COLUMN` in 2 files | Canonical copy in `src/config.py` | Eliminates drift between `errant_analysis.py` and `generate_report.py`. |
| **Python** | 3.12 (implicit) | 3.14 (explicit) | Latest stable; all deps must have 3.14 wheels. |
| **Linter** | `ruff` (existing) | No change | Adequate. |
| **Test runner** | `pytest` (existing) | No change + `pytest-cov` | Add coverage measurement. |
| **Execution** | `subprocess` + CLI | Pure Python (eliminate Typst subprocess) | Remove fragile external process dependency. |

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── config.py              # NEW — shared constants, env loading, error code maps
│   ├── models.py              # NEW — Pydantic BaseModels for all data shapes
│   ├── _retry.py              # KEEP — retry decorator
│   ├── ingest.py              # MODIFY — use config.py, response_format, model_validate
│   ├── errant_analysis.py     # MODIFY — use config.py, response_format, model_validate
│   ├── generate_report.py     # REWRITE — Jinja2→Playwright, remove Typst
│   ├── batch_errant_upsert.py # MODIFY — use config.py, model_validate
│   ├── migrate_writing_records.py   # KEEP (no changes needed)
│   ├── rename_json_files.py   # MODIFY — use config.py
│   ├── interpret_results.py   # KEEP (research analysis, not pipeline)
│   ├── desk_statistics.py     # KEEP (research analysis, not pipeline)
│   ├── preflight_check.py     # KEEP
│   ├── research_prep.py       # KEEP
│   ├── sampling_strategy.py   # KEEP
│   ├── setup_error_analysis.py # KEEP
│   ├── supabase_sql.py        # KEEP
│   ├── pilot_prep.py          → MOVE to scripts/archive/
│   ├── query_class_mapping.py → MOVE to scripts/archive/
│   ├── query_skill_count.py   → MOVE to scripts/archive/
│   ├── write_historical_data.py → MOVE to scripts/archive/
│   ├── test_models.py         → MOVE to scripts/archive/
│   ├── add_word_count.py      → MOVE to scripts/archive/
├── tests/
│   ├── test_ingest.py         # EXPAND — use model fixtures
│   ├── test_errant.py         # EXPAND — add response_format tests
│   ├── test_rename_json_files.py  # KEEP
│   ├── test_report.py         # REWRITE — test Playwright path instead of Typst
│   ├── test_config.py         # NEW
│   ├── test_models.py         # NEW
│   └── fixtures/
│       └── error_golden.json  # KEEP
├── templates/
│   └── report.html            # NEW — Jinja2 report template
├── scripts/archive/           # NEW
│   ├── README.md              # Document each moved script
│   ├── pilot_prep.py
│   ├── query_class_mapping.py
│   ├── query_skill_count.py
│   ├── write_historical_data.py
│   ├── test_models.py
│   └── add_word_count.py
├── requirements.txt           # ADD — playwright, jinja2, pydantic. REMOVE — typst, pypdf
├── .specify/specs/001-codebase-evaluation/
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
│       └── ...
```

## Architecture Overview

```
               ┌─────────────┐
               │  config.py  │  ← single source of truth
               │  models.py  │  ← Pydantic schema definitions
               └──────┬──────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌────────┐      ┌───────────┐      ┌──────────┐
│ ingest │      │  errant   │      │generate  │
│   .py  │ ──→  │_analysis  │ ──→  │_report   │
│  OCR   │      │   .py     │      │   .py    │
│ Gemini │      │ DeepSeek  │      │Jinja2→   │
│        │      │ + ERRANT  │      │Playwright│
└────────┘      └─────┬─────┘      │ → PDF    │
                      │            └──────────┘
                      ▼
              ┌──────────────┐
              │   Supabase   │
              │ error_reports│
              └──────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Days 1-2)

**Goal**: Create shared infrastructure without changing existing pipeline behavior.

| Step | Files | Description | Test |
|------|-------|-------------|------|
| 1.1 | `src/config.py` | Move all shared constants: env vars, paths, model names, error code mappings. Deduplicate `ERRANT_CODE_TO_NAMES` and `ERRANT_CODE_TO_COLUMN`. | `test_config.py` |
| 1.2 | `src/models.py` | Define `IngestionOutput`, `ErrantOutput`, `ReportData`, `ErrantAnalysis`, `Metadata` models with `field_validator` decorators. | `test_models.py` |
| 1.3 | `requirements.txt` | Add `playwright`, `jinja2`, `pydantic`, `pixelmatch`. Remove `typst`, `pypdf`. | `pip install -r requirements.txt` |
| 1.4 | `scripts/archive/` | Move 6 one-shot scripts. Create README.md with purpose/last-use docs. | `ls scripts/archive/` |

### Phase 2: LLM & Data Integrity (Day 2-3)

**Goal**: Add response_format and Pydantic validation without changing behavior.

| Step | Files | Description | Test |
|------|-------|-------------|------|
| 2.1 | `src/ingest.py` | Add `response_format={"type": "json_object"}` to OpenRouter call. Already has JSON parsing fallback — keep as safety net. Validate output via `IngestionOutput.model_validate()` before write. | `test_ingest.py` |
| 2.2 | `src/errant_analysis.py` | Add `response_format` to correction and summary LLM calls. Validate `_finalize_output` output via `ErrantOutput.model_validate()` before write. | `test_errant.py` |
| 2.3 | `src/batch_errant_upsert.py` | Validate via `ErrantOutput` model before upsert. | `test_errant.py` |
| 2.4 | `src/ingest.py`, `errant_analysis.py` | Refactor `_call_api` and `call_openrouter` to use `config.py` for model names, API keys, timeouts. | Smoke tests |

### Phase 3: PDF Pipeline Replacement (Days 3-6)

**Goal**: Replace Typst compilation with Jinja2→Playwright. This is the highest-risk, highest-ROI change.

| Step | Files | Description | Test |
|------|-------|-------------|------|
| 3.1 | `templates/report.html` | Create Jinja2 template reproducing current Typst layout: masthead grid with logos, chart image, corrected markup with `<u>` tags, original text, summary. CSS `@page { size: A4; margin: 1.5cm; }` with `@media print` page breaks. | `test_report.py` |
| 3.2 | `src/generate_report.py` | Replace `build_typ_header()` + `build_student_block()` with `jinja2.Environment` + `playwright` pipeline. Keep `generate_chart()` unchanged (matplotlib → PNG). Keep `fetch_historical_data()` unchanged. | `test_report.py` |
| 3.3 | — | Pixel-diff the new Playwright PDF against a saved Typst baseline. Tune CSS until `<1%` pixel difference on same student data. | Manual visual check |
| 3.4 | `src/generate_report.py` | Remove `typst compile` subprocess call, `build_typ_header()`, `build_student_block()` functions, `pypdf` fallback. Clean up unused imports. | `pytest tests/` |

### Phase 4: Test Expansion (Days 6-8)

**Goal**: Smoke tests for all 21 modules (15 after archiving), >60% coverage on core modules.

| Step | Files | Description |
|------|-------|-------------|
| 4.1 | `tests/test_config.py` | Test all config paths exist, env var loading, error code mapping completeness |
| 4.2 | `tests/test_models.py` | Test each Pydantic model: valid data, invalid data, edge cases |
| 4.3 | `tests/test_report.py` | Expand to test Playwright pipeline, Jinja2 template rendering, chart generation |
| 4.4 | `tests/test_errant.py` | Add tests for `response_format` compliance, config integration |
| 4.5 | `tests/test_ingest.py` | Add tests for `IngestionOutput` validation, config integration |
| 4.6 | Smoke tests | Create `tests/test_smoke.py` covering all remaining modules (import + one function call per module) |

### Phase 5: Verification & Cleanup (Day 8-9)

| Step | Description |
|------|-------------|
| 5.1 | Run full pipeline end-to-end with test data: `ingest → errant → report` via Playwright |
| 5.2 | Verify no `typst compile` calls: `grep -r "typst" src/` should return empty |
| 5.3 | Verify all JSON writes use `model_validate`: `grep -r "model_validate" src/` should return all write paths |
| 5.4 | Verify all LLM calls use `response_format`: `grep -r "chat.completions.create" src/ | grep response_format` |
| 5.5 | Run `ruff check src/ tests/` |
| 5.6 | Run `pytest tests/ -v --cov=src --cov-report=term` — confirm >60% coverage |

## Dependency Graph

```
ingest.py
  ├── _retry.py
  ├── config.py (new)
  └── models.py (new)

errant_analysis.py
  ├── _retry.py
  ├── config.py (new)
  ├── models.py (new)
  ├── generate_report.py (esc function only)
  ├── spacy
  └── errant

batch_errant_upsert.py
  ├── errant_analysis.py (correct_text, classify_edits, etc.)
  ├── config.py (new)
  └── models.py (new)

generate_report.py
  ├── config.py (new)
  ├── models.py (new)
  ├── jinja2
  ├── playwright
  └── matplotlib

migrate_writing_records.py ─── supabase
rename_json_files.py ─── config.py (new)
preflight_check.py (standalone)
research_prep.py ─── supabase
interpret_results.py ─── pandas, supabase
desk_statistics.py ─── pandas, scipy, matplotlib
sampling_strategy.py ─── supabase
setup_error_analysis.py ─── supabase_sql.py
supabase_sql.py ─── requests
```

No circular dependencies. All arrows flow left-to-right or top-to-bottom.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| errant/spaCy wheel unavailable for 3.14 | Medium | High | Build from source; pin known-good version |
| Playwright PDF fonts differ from Typst | Medium | Medium | Use same Roboto OTFs; `@font-face` injection |
| Jinja2 template not pixel-perfect | Medium | Medium | Iterative CSS tuning against baseline |
| Existing tests fail after refactors | Low | High | Run tests before/after each phase |
| Visual diff fails due to anti-aliasing | Medium | Low | Set pixelmatch threshold to 0.1% |
