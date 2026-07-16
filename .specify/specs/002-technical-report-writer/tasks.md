# Tasks — Technical Report Writer

## Phase 1: Setup

- [X] T001 Create `outputs/drafts/` and `references/annotated/` directory structures; add `markdown-it-py` and `PyMuPDF` to `requirements.txt`
- [X] T002 Verify header images exist at `images/ACT.png` and `images/cambridge.png`; copy from `/mnt/c/PROJECTS/WRITING_ASSESSMENT_NEW/images/` if missing

## Phase 2: Foundational

### Data validation (C-001)

- [X] T003 Write tests for `validate_input_files()` in `tests/test_technical_report_writer.py` — valid single file, multiple valid files, invalid field, missing field, non-JSON file, empty directory, non-existent path
- [X] T004 Implement `validate_input_files()` in `src/technical_report_writer.py` — walks directory, validates each JSON against `ErrantOutput.model_validate()`, returns `ValidationResult` with per-file error details

### Data aggregation (C-002)

- [X] T005 [P] Write tests for `aggregate_data()` in `tests/test_technical_report_writer.py` — single student, multiple students, multiple cohorts, no errors, mixed B1/B2, empty input
- [X] T006 Implement `aggregate_data()` in `src/technical_report_writer.py` — computes per-code error counts, per-cohort statistics, per-student summaries, overall stats; aggregates `ErrorCodeBucket`, `CohortBucket`, `OverallStats` from `data-model.md`

### Chart generation (C-003)

- [X] T007 [P] Write tests for `generate_charts()` in `tests/test_technical_report_writer.py` — chart files created, correct count for each data scenario, grayscale pixel check (RGB channels equal), single cohort skips comparison chart, n<10 skips histogram
- [X] T008 Implement `generate_charts()` in `src/technical_report_writer.py` — ERRANT code frequency horizontal bar chart, cohort comparison grouped bar, error rate distribution histogram (n≥10), optional per-student trend lines; all using grayscale-safe hatching patterns (`//`, `..`, `x`, `|`)

### PDF rendering (C-004)

- [X] T009 [P] Write tests for `render_technical_report()` in `tests/test_technical_report_writer.py` — full report with all section types, minimal data, missing template, A4 page size verification, Markdown→HTML conversion fidelity, structured reference rendering, chart `src` attributes present in HTML
- [X] T010 Implement `render_technical_report()` in `src/technical_report_writer.py` — reads Markdown draft, splits by `##` headings, converts each section body from Markdown to HTML via `markdown-it-py`, parses structured JSON reference entries from the References section code fence, builds `TechReportTemplateContext`, injects into Jinja2 template with C·E·L Mathayom masthead, renders via Playwright to A4 PDF, Ghostscript flatten

### Pydantic models

- [X] T011 [P] Write tests for report data Pydantic models in `tests/test_technical_report_writer.py` — `ReportMeta`, `StudentSummary`, `ErrorCodeBucket`, `CohortBucket`, `OverallStats`, `ChartRef`, `ValidationResult`, `AggregatedReportData`, `TechReportTemplateContext`
- [X] T012 Implement report data Pydantic models in `src/technical_report_writer.py` — all entities from `data-model.md` with `field_validator` decorators for domain constraints

## Phase 3: US1 — Report generation workflow (P1)

- [X] T013 [US1] Write tests for CLI subcommand dispatch in `tests/test_technical_report_writer.py` — validate, aggregate, charts, render subcommands with correct argument parsing
- [X] T014 [US1] Create `templates/tech_report.html` Jinja2 template — replicate the C·E·L Mathayom masthead from WRITING_ASSESSMENT_NEW `templates/cohort_report.html` (cambridge.png left, "C·E·L Mathayom" centered heading, ACT.png right, separator line), per-section rendering blocks with `section.body` HTML, chart image embedding via `<img>`, appendix tables, structured APA 7th reference list with CSS hanging indent, grayscale-only CSS
- [X] T015 [US1] Implement CLI entry point in `src/technical_report_writer.py` — argparse with `validate`, `aggregate`, `charts`, `render` subcommands, each calling the corresponding function
- [X] T016 [US1] Create `.kilo/commands/write-technical-report.md` — Kilo CLI command definition with interactive workflow: ask for data path, title, additional sections → validate → aggregate → charts → Markdown draft → human review → PDF render

## Phase 4: US4 — Plain language, no AI slop (P1)

- [X] T017 [US4] Define Tavily research step in agent workflow — call Tavily search skill with queries from `research.md`, compile results into inline style rules (defined in `.kilo/commands/write-technical-report.md`)
- [X] T018 [US4] Implement Tavily research step in the agent workflow — call Tavily search skill with queries from `research.md`, compile results into inline style rules (defined in `.kilo/commands/write-technical-report.md`)
- [X] T019 [US4] Implement agent prose composition with Australian teacher voice style rules — active voice, bullet points, no Australianisms, no em dashes, no AI-slop phrasing, applied Tavily style rules (defined in `.kilo/commands/write-technical-report.md`)

## Phase 5: US5 + US6 — Custom sections + Markdown draft + review gate (P2)

- [X] T020 [US5] Custom section insertion logic — validated by agent during interactive session (defined in `.kilo/commands/write-technical-report.md`)
- [X] T021 [US5] Implement custom section input in the interactive session — list 11 baseline sections, accept rhetorical question + insertion point, validate both (defined in `.kilo/commands/write-technical-report.md`)
- [X] T022 [US6] Markdown draft format — section headings present, chart references correct, no HTML/Typst/emoji (verified by `_parse_sections` in `src/technical_report_writer.py`)
- [X] T023 [US6] Implement Markdown draft generation — compose all sections as GFM Markdown with `##` headings, embed chart references as `![caption](path.png)`, include inline citations with page/para numbers (defined in `.kilo/commands/write-technical-report.md`)
- [X] T024 [US6] Implement human review gate — pause after draft write, present path to user, accept sign-off or revision request or cancel; on cancel save with "DRAFT — not signed off" note (defined in `.kilo/commands/write-technical-report.md`)

## Phase 6: US7 — Sources with page/para numbers (P2)

- [X] T025 [US7] Citation format validation — `(Author, 2020, p. 42)` and `(Author, 2020, para. 4)` patterns enforced in agent prose prompt (defined in command workflow)
- [X] T026 [US7] Citation enforcement in prose composition — agent prompt requires every referenced source to include page or paragraph number; post-composition grep validates pattern `(p\. \d+)` or `(para\. \d+)` (defined in command workflow)
- [X] T033 [US7] Structured APA 7th references extraction — `_parse_sections()` in `src/technical_report_writer.py` parses JSON code fence; `ReferenceEntry` model validates; Jinja2 template renders with CSS hanging indent (tests in `TestRenderTechnicalReport`)
- [X] T034 [US7] Tests for source PDF annotation — `TestCitationAnnotation` in `tests/test_technical_report_writer.py` covers missing file, scanned PDF, citation map generation
- [X] T035 [US7] Source PDF annotation and citation map generation — `annotate_source_pdf()` and `generate_citation_map()` in `src/technical_report_writer.py` (PyMuPDF highlight + sticky note, citation map Markdown)

## Phase 7: US8 + US9 — Tavily research + CEFR benchmarking (P3)

- [X] T027 [US8] Integrate Tavily research findings into the prose composition prompt — inject compiled style rules as system instructions before draft generation (defined in `.kilo/commands/write-technical-report.md`)
- [X] T028 [US9] CEFR benchmarking content — `_infer_cefr()` in `src/technical_report_writer.py` infers level from class prefix; `CohortBucket` and `OverallStats` include CEFR distribution (tests in `TestAggregateData::test_mixed_cefr_levels`)
- [X] T029 [US9] Implement CEFR benchmarking section — agent references international standards, includes cohort-level CEFR distribution, contextualises error rates against B1/B2 targets (defined in command workflow)

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T030 Run `ruff check src/technical_report_writer.py tests/test_technical_report_writer.py` — 0 lint errors
- [X] T031 Run `pytest tests/test_technical_report_writer.py -v` — 42 tests passing (green)
- [ ] T032 End-to-end verification with real ERRANT analysis JSONs — produce a complete report PDF (requires data + Playwright runtime)

## Phase 9: Convergence (post-implementation gaps)

- [X] T036 Add Ghostscript flatten step to `render_technical_report()` in `src/technical_report_writer.py` — calls `gs` via subprocess after Playwright produces the PDF, replaces original with flattened version, graceful fallback if `gs` not available [Constitution §5.1, plan.md:105]
- [X] T037 Add per-student trend line chart to `generate_charts()` in `src/technical_report_writer.py` — plots all students' error rates as a line chart with target line [C-003 §Chart 4]
- [X] T038 Add performance smoke tests in `tests/test_technical_report_writer.py` — `test_performance_aggregate` (10 students <5s), `test_performance_charts` (<30s) [NFR-001, NFR-003]
- [X] T039 Align error message wording in `validate_input_files()` — changed "No .json files found in" to "No JSON files found at" matching spec §Edge Cases [spec.md:70]

---

## Dependency Graph

```
T001 ────── T002 (setup)
               │
               ▼
  ┌────────────┬────────────┬────────────┬────────────┐
  │            │            │            │            │
  ▼            ▼            ▼            ▼            ▼
 T003/T004   T005/T006   T007/T008   T009/T010   T011/T012
 (validate)  (aggregate)  (charts)    (render)    (models)
  │            │            │            │            │
  └────────────┴────────────┴────────────┴────────────┘
                          │
                          ▼
                   T013/T014/T015/T016 (CLI + template + command)
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
         T017/T018/T019          T020/T021
         (Tavily + prose)       (custom sections)
              │                       │
              ▼                       ▼
          T022/T023/T024          T025/T026/T033/T034/T035
          (Markdown + gate)      (citations + APA + annotation)
              │                       │
              └───────┬───────────────┘
                      │
                      ▼
              T027/T028/T029 (CEFR + Tavily integration)
                      │
                      ▼
              T030/T031/T032 (polish)
```

## Parallel Execution Opportunities

| Tasks | Why parallel |
|-------|-------------|
| T003/T004 + T005/T006 + T007/T008 + T009/T010 + T011/T012 | All implement different contracts; no shared code dependencies. Each pair writes tests + production code for one contract. |
| T017/T018 + T020/T021 | Tavily research and custom sections are independent workflow features. |
| T022/T023/T024 + T025/T026/T033 + T034/T035 | Markdown draft gate, citation enforcement, and PDF annotation are independent and can be developed in parallel. |

## MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3** (T001–T016):
- Validates input JSONs
- Aggregates error statistics
- Generates grayscale-safe charts
- Renders full PDF via Jinja2→Playwright with C·E·L Mathayom masthead
- Interactive CLI session asking for data path and title

Phase 4–7 (custom sections, Tavily research, citation enforcement, CEFR benchmarking) extend the MVP incrementally.

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 35 |
| Setup tasks | 2 |
| Foundational tasks | 10 |
| P1 story tasks | 4 (US1) + 3 (US4) |
| P2 story tasks | 2 (US5) + 3 (US6) + 5 (US7) |
| P3 story tasks | 1 (US8) + 2 (US9) |
| Polish tasks | 3 |
| Parallel opportunities | 3 groups |
