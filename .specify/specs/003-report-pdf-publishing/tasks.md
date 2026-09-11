# Tasks — Report PDF Publishing

## Phase 0: Spec artifacts & pre-implementation drift

- [ ] T001 Write `.specify/specs/003-report-pdf-publishing/spec.md` (FR-001…FR-009, NFRs, edge cases, clarifications); fold the `templates/tech_report.html` inline-opacity point into FR-003
- [ ] T002 Write `plan.md`, `tasks.md`, `checklists/` for 003
- [ ] T003 Pre-implementation drift: spec ↔ plan ↔ tasks forward/reverse reconciliation

## Phase 1: Setup / baseline

- [ ] T004 [P] Capture baseline PDFs (one class folder, both pipelines) to `outputs/baseline-003/` for before/after comparison
- [ ] T005 [P] Confirm Pillow present; no `requirements.txt` change expected

## Phase 2: Foundational — opaque image helper

- [ ] T006 [P] Write `tests/test_image_utils.py` — RGBA, LA, P-with-transparency, RGB passthrough, missing file
- [ ] T007 Implement `src/image_utils.py` — `opaque_png_bytes()`, `opaque_data_uri()`

## Phase 3: US1 — Ghostscript-free rendering

- [ ] T008 Remove gs flatten block (`technical_report_writer.py:547-558`) and unused `subprocess` import
- [ ] T009 Remove `_flatten_pdf` (334-359) + `_pad_and_merge_pdfs` (319-331) from `generate_report.py`; drop unused `fitz`/`mimetypes` imports
- [ ] T010 [P] Test: static guard — no `pdfwrite`, `"gs"`, or `subprocess` in either module
- [ ] T011 Render both pipelines with `gs` absent from PATH; verify success + non-empty PDFs

## Phase 4: US2 — Opaque images & alpha-free charts

- [ ] T012 [P] Wire `image_utils.opaque_data_uri` into `generate_report._file_to_data_uri`
- [ ] T013 [P] Wire `image_utils.opaque_data_uri` into `technical_report_writer._img_b64`
- [ ] T014 Replace `axhspan(alpha=0.18)` with opaque `#f6f6f6`; explicit `facecolor="white"`, `transparent=False` in `generate_chart`
- [ ] T015 Add `facecolor="white"`, `transparent=False` to tech-writer `savefig` calls
- [ ] T016 Strip all 22 inline-SVG `opacity`/`stroke-opacity`/`fill-opacity` in `templates/tech_report.html` via over-white pre-blend
- [ ] T017 [P] Test: `generate_report` chart SVG has no `opacity:` and has a `#ffffff` background
- [ ] T018 Fix `test_charts_grayscale` to parse SVG text — assert grayscale hex + no opacity attrs
- [ ] T019 PDF-level verification: outputs contain no `/SMask` and no transparent `/Group` flag; A4 page size (595.28×841.89 pt) preserved [NFR-003]; per-student runtime delta < 50 ms [NFR-002]

## Phase 5: US3 — Single-file per-student output

- [ ] T020 Remove merge/delete/flatten block in `main`; retain individual PDFs; update summary prints
- [ ] T021 Test: N students → N PDFs, no `*-errant-report.pdf`, page counts unpadded
- [ ] T022 Verify filename pattern `{dd-mm-yy}-{HHMM}-{class}-{sid}.pdf`

## Phase 6: Documentation

- [ ] T023 Update `.opencode/skills/local-report/SKILL.md` (frontmatter, remove merge/gs sections, output/compat)
- [ ] T024 Update `.opencode/command/local-report.md` (single-file wording)
- [ ] T025 Update `AGENTS.md` merge/flatten gotcha

## Phase 7: Polish & convergence

- [ ] T026 `ruff check src/ tests/` — clean
- [ ] T027 `pytest tests/ -v` — record results; known-failure count should drop by 1
- [ ] T028 End-to-end render of a real class folder; open in Acrobat, confirm no flattening prompt
- [ ] T029 Convergence report — FR-by-FR verification + forward/reverse drift

---

## Dependency Graph

```
T001→T002→T003
              │
              ▼
        T004/T005 (baseline)
              │
              ▼
        T006/T007 (image helper)
              │
      ┌───────┴────────┐
      ▼                ▼
T008–T011 (no-gs)  T012–T019 (opaque/alpha-free)
      └───────┬────────┘
              ▼
        T020–T022 (single-file)
              │
              ▼
        T023–T025 (docs)
              │
              ▼
        T026–T029 (polish + convergence)
```

## Parallel Execution Opportunities

| Tasks | Why parallel |
|-------|-------------|
| T012 + T013 | Independent call sites, same helper already built. |
| T008/T010 + T014/T017 | gs removal and chart opacity touch different code regions. |
| T023 + T024 + T025 | Independent docs. |

## MVP Scope

**T001–T022** — helper + gs-free + opaque images + single-file output. Docs (T023–T025) and convergence (T029) complete the deliverable.

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 29 |
| Setup | 2 |
| Foundational | 2 |
| US1 (no gs) | 4 |
| US2 (opaque/alpha-free) | 8 |
| US3 (single-file) | 3 |
| Docs | 3 |
| Polish + convergence | 4 |
| Parallel groups | 3 |
