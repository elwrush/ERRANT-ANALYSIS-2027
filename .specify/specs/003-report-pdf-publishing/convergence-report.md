# Report PDF Publishing — Convergence Report

**Date:** 2026-09-11
**Scope:** `.specify/specs/003-report-pdf-publishing/spec.md` ↔ implementation
**Verdict:** ✅ **Converged** — all FR/NFR met; no unresolved forward drift.

## Functional Requirements

| FR | Status | Evidence |
|----|--------|----------|
| FR-001 no Ghostscript | ✅ Met | `grep -rn "pdfwrite\|subprocess" src/generate_report.py src/technical_report_writer.py` → none. Both pipelines rendered successfully with a failing `gs` shim first on `PATH`. Static guard `TestNoGhostscript` passes. |
| FR-002 opaque raster images | ✅ Met | `src/image_utils.py` composites RGBA/LA/P-with-transparency over white and re-encodes RGB PNG; both `_file_to_data_uri` and `_img_b64` delegate to it. Logos decode to `RGB`. `test_image_utils.py` (7 tests) passes. |
| FR-003 alpha-free charts | ✅ Met | `generate_chart` uses opaque `#f6f6f6` + `transparent=False, facecolor="white"`; tech-writer charts force opaque white background and `framealpha=1.0`. `templates/tech_report.html` has 0 `opacity` / 0 `rgba(`. `report.html` and `m2_3b_report.html` were already clean. All chart SVGs report 0 opacity attributes. |
| FR-004 single-file output | ✅ Met | Merge/pad/flatten block removed from `main()`. End-to-end `python src/generate_report.py "E2E-003"` → 2 standalone PDFs, no `*-errant-report.pdf`. `TestSingleFileOutput` passes. |
| FR-005 retain individuals | ✅ Met | `p.unlink()` loop removed; e2e confirmed both files retained. |
| FR-006 naming unchanged | ✅ Met | E2E filenames `11-09-26-0840-M3-5A-90001.pdf` match `^\d{2}-\d{2}-\d{2}-\d{4}-.+-<sid>\.pdf$`; asserted in `TestSingleFileOutput`. |
| FR-007 console output | ✅ Met | "Merged"/"Flattened" prints removed; summary now reports "N standalone PDF(s)". |
| FR-008 docs | ✅ Met | `local-report/SKILL.md`, `.opencode/command/local-report.md`, and `AGENTS.md` updated; no residual merge/gs claims (only explicit negations). |
| FR-009 tests | ✅ Met | Static guard added; `test_image_utils.py` added (7); chart alpha-free test added; `test_charts_grayscale` rewritten to parse SVG text and now passes. |

## Non-Functional Requirements

| NFR | Status | Evidence |
|-----|--------|----------|
| NFR-001 no new dependency | ✅ Met | `requirements.txt` unchanged; Pillow already present (12.3.0). |
| NFR-002 negligible runtime delta | ✅ Met | Per-student render ~1.40 s; compositing 3 images is sub-millisecond. |
| NFR-003 A4 preserved | ✅ Met | Final PDFs 595.9 × 842.9 pt (matches baseline). |
| NFR-004 no gs prerequisite | ✅ Met | Rendered with a failing `gs` shim first on `PATH`. |
| NFR-005 no quality loss | ✅ Met | Charts remain vector SVG; text remains vector. |
| NFR-006 no new subprocess/network | ✅ Met | Static guard passes; no new calls. |

## PDF Transparency Evidence

| PDF | `/SMask` | `/Transparency` |
|-----|----------|-----------------|
| baseline per-student (pre-change) | 2 | 0 |
| baseline tech report (pre-change) | 0 | 3 |
| **final per-student** | **0** | **0** |
| **final tech report** | **0** | **0** |

## Test Results

`pytest tests/ -q` → **246 passed, 4 failed**. The 4 failures are all pre-existing and documented in `AGENTS.md` (`test_esc_handles_special_chars`, `test_missing_template_raises`, `test_render_subcommand_missing_draft`, `test_citation_map_generated`). The known-failure count dropped by 1 (`test_charts_grayscale` now green), as predicted.

`ruff check src/ tests/` → **All checks passed**.

## Forward Drift (spec → code)

None outstanding. NFR-002/NFR-003 were initially uncovered by a task; T019 was expanded to include the A4 size and runtime checks (reconciled in T003).

## Reverse Drift (code → spec)

| Item | Assessment |
|------|------------|
| `opaque_data_uri` passes SVG through unchanged | Consistent with FR-002 (raster only) + FR-003 (SVG made alpha-free at generation). Recorded here; not a spec gap. |
| `framealpha=1.0` on the cohort legend | The matplotlib legend frame was an additional transparency source not individually enumerated. Covered by FR-003 ("Charts MUST contain no transparency"). |
| `templates/tech_report.html` inline opacity | Folded into FR-003 before implementation (T003). |
| Stray PIL/SVG block appended to `TestCitationAnnotation::test_citation_map_generated` | Pre-existing defect, out of scope for 003. Not fixed; flagged for a future change. |

## Conclusion

The implementation matches the spec. Every FR and NFR is satisfied or verified, no forward drift remains, and the only reverse-drift items are either explicitly covered by FR-003 or pre-existing and out of scope. **Converged.**
