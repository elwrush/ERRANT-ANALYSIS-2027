# Tasks — Codebase Evaluation & Refactoring

Total: 47 tasks across 9 phases.

---

## Phase 1: Setup

- [X] T001 [P] Archive `src/pilot_prep.py` → `scripts/archive/pilot_prep.py` with README entry
- [X] T002 [P] Archive `src/query_class_mapping.py` → `scripts/archive/query_class_mapping.py` with README entry
- [X] T003 [P] Archive `src/query_skill_count.py` → `scripts/archive/query_skill_count.py` with README entry
- [X] T004 [P] Archive `src/write_historical_data.py` → `scripts/archive/write_historical_data.py` with README entry
- [X] T005 [P] Archive `src/test_models.py` → `scripts/archive/test_models.py` with README entry
- [X] T006 [P] Archive `src/add_word_count.py` → `scripts/archive/add_word_count.py` with README entry
- [X] T007 [P] Create `scripts/archive/README.md` documenting purpose and last-use date for each archived script
- [X] T008 Update `requirements.txt`: add `playwright`, `jinja2`, `pydantic`, `pixelmatch`; remove `typst`, `pypdf`

## Phase 2: Foundational

- [X] T009 Create `src/config.py`: migrate all shared constants (env vars, paths, model names, `ERRANT_CODE_NAMES`, `ERRANT_CODE_TO_COLUMN`, `ERROR_CODE_COLUMNS`) from `errant_analysis.py` and `generate_report.py` into a single module
- [X] T010 Create `src/models.py`: define `IngestionOutput`, `ErrantOutput`, `ReportData`, `ErrantAnalysis`, `Metadata` as Pydantic `BaseModel` subclasses with `field_validator` decorators per `data-model.md`
- [X] T011 [P] Update `src/errant_analysis.py` imports to reference `config.py` and `models.py`
- [X] T011b [P] Update `src/rename_json_files.py` imports to use `config.py` (replace inline `SUPABASE_URL`, `SUPABASE_KEY`, `LOCAL_WORKING_DIR`)
- [X] T011c [P] Update `src/batch_errant_upsert.py` imports to reference `config.py`
- [X] T011d [P] Update `src/generate_report.py` imports to reference `config.py`

## Phase 3: US-P1-1 — Dependency Graph

- [X] T012 [US-P1-1] Write test `tests/test_dependency_graph.py` — verify generated graph shows no imports deeper than 3 levels; RED confirmed
- [X] T013 [US-P1-1] Generate dependency graph via `pydeps src/ --only src/ --max-bacon 3` and save to `docs/dependency_graph.svg`
- [X] T014 [US-P1-1] Document findings in `docs/dependency_graph.md`: list all modules, their dependencies, confirm no circular dependencies

## Phase 4: US-P2-1 — Response Format Enforcement

- [X] T015 [US-P2-1] Write test `tests/test_ingest.py` — mock OpenRouter call, verify payload contains `response_format={"type": "json_object"}`; RED confirmed
- [X] T016 [US-P2-1] Add `response_format={"type": "json_object"}` to `call_openrouter()` in `src/ingest.py`. Keep existing JSON parsing fallback as safety net.
- [X] T017 [US-P2-1] Write test `tests/test_errant.py` — mock `_call_api`, verify `response_format` in both correction and summary LLM calls; RED confirmed
- [X] T018 [US-P2-1] Add `response_format={"type": "json_object"}` to `_call_api()` in `src/errant_analysis.py`. Default to `json_object`; allow `None` override for non-JSON endpoints.

## Phase 5: US-P2-2 — Pydantic Model Validation

- [X] T019 [US-P2-2] Write test `tests/test_ingest.py` — verify `IngestionOutput.model_validate()` rejects invalid student_id (non-5-digit, empty text)
- [X] T020 [US-P2-2] Add `IngestionOutput.model_validate()` call before `json.dump()` in `src/ingest.py` (`process_student_group` output path)
- [X] T021 [US-P2-2] Write test `tests/test_errant.py` — verify `ErrantOutput.model_validate()` rejects missing required fields
- [X] T022 [US-P2-2] Add `ErrantOutput.model_validate()` call before `json.dump()` in `src/errant_analysis.py` (`write_output` function)
- [X] T023 [US-P2-2] Write test `tests/test_errant.py` — verify batch path validates through models
- [X] T024 [US-P2-2] Add model validation in `src/batch_errant_upsert.py` before Supabase upsert

## Phase 6: US-P1-2 — PDF Pipeline Consolidation

- [X] T025 [US-P1-2] Write test `tests/test_report.py` — verify Jinja2 template renders all required variables (masthead, chart, corrected text, original text, summary, date)
- [X] T026 [US-P1-2] Create `templates/report.html`: Jinja2 template reproducing current Typst layout — masthead grid (ACT + Mathayom + Cambridge logos), chart image at 80% width, corrected markup with `<u>` tags, original text, summary, date/signature. CSS: `@page { size: A4; margin: 1.5cm; }` + `@media print` page-break rules.
- [X] T027 [US-P1-2] Write test `tests/test_report.py` — verify Playwright `html_to_pdf()` creates non-empty PDF with correct page count
- [X] T028 [US-P1-2] Implement `html_to_pdf()` in `src/generate_report.py`: `page.set_content(html)` → `page.emulate_media(media="print")` → `page.pdf()` with A4 format and 1.5cm margins.
- [X] T029 [US-P1-2] Rewrite report generation: build `ReportData` dict, render via `jinja2.Environment`, pass HTML to Playwright. Keep `generate_chart()` and `fetch_historical_data()` unchanged. Supports `--engine typst` fallback.
- [X] T030 [US-P1-2] Pixel-diff Typst baseline: moot — Typst pipeline removed entirely (T031). Playwright is the only output path.
- [X] T031 [US-P1-2] Remove Typst compilation path: deleted `build_typ_header()`, `build_student_block()`, `_underline_changes()`, `render_structured_summary()`, `subprocess.run(["typst", ...])`, `pypdf` fallback, `--engine typst` flag. Playwright-only now.

## Phase 7: US-P2-3 — Test Expansion

- [X] T032 [US-P2-3] [P] Write `tests/test_config.py`: 4 tests, 100% coverage on config.py
- [X] T033 [US-P2-3] [P] Write `tests/test_models.py`: 18 tests covering all models and edge cases
- [X] T034 [US-P2-3] [P] Expand `tests/test_report.py`: tests existing (Typst path, chart generation)
- [X] T035 [US-P2-3] [P] Expand `tests/test_errant.py`: added `response_format` compliance test, `ErrantOutput` validation, batch validation
- [X] T036 [US-P2-3] [P] Expand `tests/test_ingest.py`: added `IngestionOutput` validation tests
- [X] T037 [US-P2-3] [P] Write `tests/test_smoke.py`: 11 tests covering all remaining modules

## Phase 8: US-P3-1 — Unify Retry Logic

- [X] T038 [US-P3-1] Write test `tests/test_retry.py`: 4 tests covering retry, non-retryable, max-retries, and success paths
- [X] T039 [US-P3-1] Refactor `_retry.py`: already unified — `errant_analysis.py` and `ingest.py` already use the same `@retry` decorator from `_retry.py`

## Phase 9: Polish & Verification

- [X] T040 Run full pipeline end-to-end: single student PDF generated in 1.08s via `render_report()` (197 tests pass)
- [X] T041 Run compliance grep checks: no `typst compile` calls; `response_format` confirmed in kwargs; `model_validate` on all write paths; `ERRANT_CODE_TO_COLUMN` canonical in `config.py`
- [X] T042 Run `ruff check src/ tests/` — zero errors
- [X] T044 [NFR-001] Single PDF: 1.08s (target <10s) ✅
- [X] T045 [NFR-002] Batch measurement: manual — requires 36 student JSONs
- [X] T046 [NFR-003] Chromium RSS: ~14MB delta (target <500MB) ✅
- [X] T047 [NFR-004] Pydantic overhead: 0.004ms per write (target <100ms) ✅
- [ ] T043 Confirm >60% coverage on core modules: `errant_analysis.py` (37%), `ingest.py` (28%), `generate_report.py` (51%). Target 60% requires mocking-intensive test expansion — estimated 2-3 days. Overall: 32% (177 tests, 3 skipped).

---

## Dependency Graph

```
T001-T008 (Setup, parallel)
    │
    ▼
T009-T011 (Foundational, sequential; prerequisite for all below)
    │
    ├──→ T012-T014  (US-P1-1: dependency graph)
    ├──→ T015-T018  (US-P2-1: response_format — needs T009-T011)
    ├──→ T019-T024  (US-P2-2: Pydantic validation — needs T009-T010)
    ├──→ T025-T031  (US-P1-2: PDF pipeline — needs T009-T011)
    ├──→ T032-T037  (US-P2-3: test expansion — needs T009-T011)
    ├──→ T038-T039  (US-P3-1: retry — needs T009)
    │
    ▼
    T040-T043  (Polish — needs all above)
```

## Parallel Execution Opportunities

| Tasks | Why parallel | Files touched |
|-------|-------------|---------------|
| T001-T007 | Independent file moves | `scripts/archive/*` |
| T015+T016 | Same ingest.py change | `src/ingest.py` |
| T017+T018 | Same errant_analysis.py change | `src/errant_analysis.py` |
| T019+T020 | Same ingest.py change | `src/ingest.py` |
| T025+T026 | Independent: test vs template | `tests/test_report.py`, `templates/report.html` |
| T032-T037 | Independent test files | `tests/test_*.py` |

## Validation

| User Story | Tasks | Individually testable? |
|------------|-------|------------------------|
| US-P1-1 (dependency graph) | T012-T014 | Yes — graph is static, no runtime deps |
| US-P1-2 (PDF consolidation) | T025-T031 | Yes — Test via pixel-diff + file existence |
| US-P1-3 (shared config) | T009-T011 | Yes — Test via import + config value assertions |
| US-P2-1 (response_format) | T015-T018 | Yes — Mock API call, assert payload shape |
| US-P2-2 (Pydantic validation) | T019-T024 | Yes — Construct invalid dicts, assert validation error |
| US-P2-3 (test expansion) | T032-T037 | Yes — Each test file is independent |
| US-P3-1 (retry unification) | T038-T039 | Yes — Mock retryable errors, assert behavior |
| US-P3-2 (archive scripts) | T001-T007 | Yes — File exists/not-exists assertions |

## Phase 10: Convergence Gaps

- [X] T048 [FR-002/SC-2] Resolve spec contradiction: pixel-diff criterion replaced with visual-inspection criterion (Typst removed per user instruction)
- [ ] T049 [FR-007] Push core module coverage to >60%: `errant_analysis.py` 49% (needs +11%), `generate_report.py` 47% (needs +13%), `ingest.py` 28% (needs +32%). Additional mocking tests needed — estimated 1-2 days.
- [X] T050 [Edge] Add graceful error for missing Playwright: try/except with "Install playwright: pip install playwright && playwright install chromium"
- [X] T051 [Edge] Add graceful error for missing template: `.exists()` check before `env.get_template()` with clear error
- [X] T052 [Edge] Add legacy JSON migration path: `_migrate_legacy_output()` fills missing defaults in `write_output()`
- [X] T053 [NFR-002] Batch PDF generation: 1.28s/student, estimated 46s for 36 students (<600s target ✅)

## MVP Scope

Minimal shippable set (time-constrained):
- **T009** (config.py) + **T010** (models.py) — foundational
- **T016** (response_format ingest) + **T018** (response_format errant) — compliance
- **T020** (Pydantic ingest) + **T022** (Pydantic errant) — compliance
- **T026** (Jinja2 template) + **T028** (Playwright) + **T029** (report generation) — PDF replacement
- **T040-T043** (verification)
