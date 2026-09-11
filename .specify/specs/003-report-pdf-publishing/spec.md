# Report PDF Publishing

## Feature Summary

Rework report PDF production across both report pipelines — the per-student feedback reports (`src/generate_report.py`) and the main technical/cohort report (`src/technical_report_writer.py`) — so that:

1. **Ghostscript is never invoked.** The `pdfwrite` flatten steps in both pipelines are removed.
2. **Transparency is removed at the source.** Raster logos are composited to opaque RGB PNGs, chart SVGs are alpha-free with an opaque white background, and the hard-coded inline-SVG opacity in `templates/tech_report.html` is replaced by over-white pre-blended opaque colours.
3. **Per-student reports are published as standalone single files.** Page padding, concatenation/interleaving, and the combined `*-errant-report.pdf` are removed; each student's PDF is retained on disk.

The goal is that PDFs open and print in Adobe Acrobat without a flattening prompt or flattening artefacts, with no dependency on Ghostscript being installed.

---

## User Stories

| Priority | Story |
|----------|-------|
| P1 | As a teacher, I want one standalone PDF per student that opens and prints in Adobe Acrobat without a flattening prompt, so I can distribute reports individually. |
| P1 | As a teacher, I want report generation to work on machines without Ghostscript installed, so the pipeline is portable. |
| P1 | As a teacher, I want no combined/collated booklet file, so each student's report is an independent document. |
| P2 | As a developer, I want all embedded images opaque at the source, so the generated PDF contains no transparency groups or soft masks. |
| P2 | As a school coordinator, I want the main technical report to also be Ghostscript-free and transparency-free, so both report products behave identically in Acrobat. |

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | The report pipelines MUST NOT invoke Ghostscript (`gs`) or the `pdfwrite` device. `_flatten_pdf` and its call MUST be removed from `src/generate_report.py`; the gs subprocess block MUST be removed from `src/technical_report_writer.py`. No `gs`, `pdfwrite`, or `subprocess` call for flattening may remain in either module. |
| FR-002 | All raster images embedded in report PDFs MUST be opaque. Any `RGBA`, `LA`, or `P`-with-transparency image MUST be composited over an opaque white background and re-encoded as an RGB PNG before base64 data-URI embedding. This applies to both masthead logos (`images/ACT.png`, `images/cambridge.png`) in both pipelines. |
| FR-003 | Charts MUST contain no transparency. (a) The per-student chart's translucent target band (`axhspan(..., alpha=0.18)`) MUST be replaced with an opaque, appearance-equivalent light grey (`#f6f6f6`) and saved with an opaque white background (`facecolor="white"`, `transparent=False`). (b) All `opacity`, `fill-opacity`, and `stroke-opacity` attributes in the inline SVG of `templates/tech_report.html` MUST be replaced by over-white pre-blended opaque colours. `templates/report.html` and `templates/m2_3b_report.html` are already opacity-free and MUST remain so. |
| FR-004 | `src/generate_report.py` MUST write exactly one PDF per student. It MUST NOT pad pages to a multiple of four, MUST NOT concatenate or interleave PDFs, and MUST NOT emit a combined `*-errant-report.pdf`. |
| FR-005 | Individual per-student PDFs MUST be retained on disk. The previous delete-after-merge step MUST be removed because no merge occurs. |
| FR-006 | The per-student output filename MUST remain `PDF/{folder}/{dd-mm-yy}-{HHMM}-{class}-{sid}.pdf`. |
| FR-007 | Console output MUST reflect single-file publishing: the "Merged" and "Flattened" messages MUST be removed; the final summary MUST report the number of standalone PDFs written. |
| FR-008 | Documentation MUST be updated to match the new behaviour: `.opencode/skills/local-report/SKILL.md`, `.opencode/command/local-report.md`, and `AGENTS.md`. All claims about interleaved/collated merging and Ghostscript flattening MUST be removed or corrected. |
| FR-009 | Tests MUST be updated: (a) remove merge/flatten assumptions; (b) add a static guard asserting neither report module references `pdfwrite`, a `"gs"` invocation, or `subprocess`; (c) add tests for the opaque-image helper; (d) assert chart SVGs contain no opacity attributes and have an opaque white background; (e) fix `test_charts_grayscale` to validate SVG text (grayscale hex values, no opacity attributes) instead of opening an SVG with PIL. |

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| No Ghostscript in report code | `grep -rn "pdfwrite\|Ghostscript\|subprocess" src/generate_report.py src/technical_report_writer.py` returns no flatten-related hits |
| All embedded images opaque | Decode each embedded base64 image; every image decodes to mode `RGB` (no alpha) |
| Charts alpha-free | Saved chart SVG text contains no `opacity`, `fill-opacity`, or `stroke-opacity` attributes; contains a `#ffffff` background |
| `tech_report.html` alpha-free | No `opacity`/`rgba(` occurrences remain in `templates/tech_report.html` |
| Single files only | Running `python src/generate_report.py "FOLDER"` with N students produces exactly N PDFs and no `*-errant-report.pdf` |
| No page padding | Each per-student PDF's page count equals its natural rendered length (not rounded up to a multiple of 4) |
| Naming unchanged | Filenames match `^\d{2}-\d{2}-\d{2}-\d{4}-.+-\d{5}\.pdf$` |
| Acrobat-safe | Generated PDFs contain no `/SMask` and no transparency `/Group` flag |
| Ghostscript optional | Both pipelines render successfully when `gs` is not on `PATH` |
| No new dependency | `requirements.txt` unchanged (Pillow already present) |
| Tests green | `ruff check src/ tests/` clean; `pytest tests/ -v` passes with `test_charts_grayscale` now green |

---

## Edge Cases

| Case | Expected handling |
|------|-------------------|
| Image already RGB (no alpha) | Re-encode as opaque PNG; visually unchanged |
| Palette (`P`) PNG with a `transparency` index | Convert to RGBA, composite over white, encode RGB |
| Grayscale + alpha (`LA`) PNG | Composite over white, encode RGB |
| Missing logo file | Preserve existing behaviour: `_img_b64` returns `""`; `_file_to_data_uri` raises/fails as before |
| Image larger than the page | CSS sizing rules unchanged |
| Zero students matched | Existing "No analysis output files found" error exit |
| Student with `word_count < 40` or `error_rate` None | Chart still generated; unchanged |
| `templates/report.html` / `m2_3b_report.html` | Already opacity-free; no change |
| Ghostscript not installed | Pipeline no longer references it; no fallback branch needed |
| Legacy merged PDFs already in `PDF/` | Left untouched by a new run; not deleted |
| Same-day re-run | Timestamped `{HHMM}` filenames prevent clashes |

---

## Non-Functional Requirements

| ID | Requirement | Measurement |
|----|-------------|-------------|
| NFR-001 | No new runtime dependency | `requirements.txt` unchanged; Pillow already listed |
| NFR-002 | Negligible runtime delta from PNG compositing | Per-student render time increase < 50 ms on the baseline machine |
| NFR-003 | Output remains A4 | PDF page size 595.28 × 841.89 pts (`PyMuPDF`) |
| NFR-004 | Ghostscript no longer a prerequisite | Both pipelines succeed with `gs` absent from `PATH` |
| NFR-005 | No text/chart quality loss | Charts remain vector SVG; body text remains vector |
| NFR-006 | No new subprocess or network calls | Static guard (FR-009b) passes |

---

## Key Entities

| Entity | Description |
|--------|-------------|
| Opaque image helper | `opaque_png_bytes()` / `opaque_data_uri()` in `src/image_utils.py`; composites over white and encodes RGB PNG |
| Alpha-free chart SVG | Matplotlib SVG with opaque fills and an opaque white background; no opacity attributes |
| Per-student PDF | One standalone A4 PDF per student, no padding or merge |
| Report pipeline | `src/generate_report.py` (per-student) and `src/technical_report_writer.py` (main report) |
| `tech_report.html` | Hard-coded main-report template containing inline SVG that carried opacity |

---

## Assumptions

| # | Assumption | Confidence |
|---|------------|------------|
| 1 | Pillow ≥ 10 is available (listed in `requirements.txt`). | Confirmed |
| 2 | Chromium `page.pdf()` over opaque content emits no transparency groups; verified by a PDF object scan (T019). | Medium — verify before sign-off |
| 3 | `templates/tech_report.html` is hard-coded and an opacity-only edit is safe (no structural change). | Confirmed |
| 4 | Over-white pre-blended colours preserve the rendered appearance of the original translucent elements. | Medium |
| 5 | Removing 4-page padding changes page counts; this is accepted and expected. | Confirmed |
| 6 | PyMuPDF remains a dependency for source-PDF annotation in `technical_report_writer.py`; `generate_report.py` no longer needs it. | Confirmed |
| 7 | `templates/m2_3b_report.html` remains the section-driven single-class report path. | Confirmed |

---

## Clarifications (2026-09-11)

| # | Question | Resolution | Impact on Spec |
|---|----------|------------|----------------|
| 1 | Which report pipelines does this cover? | **Both** — per-student and main technical report. | FR-001/FR-002 span both modules. |
| 2 | How is chart transparency eliminated? | Keep vector SVG but make it **alpha-free** (opaque fills + opaque white background); logos flattened to opaque RGB PNG. | FR-002, FR-003. |
| 3 | What is the deliverable? | Originally spec.md only; **superseded** — full suite (`spec.md`, `plan.md`, `tasks.md`, `checklists/`) per the always-spec-driven workflow. | N/A (process). |
| 4 | Per-student output convention? | **Drop 4-page padding; keep naming** `{dd-mm-yy}-{HHMM}-{class}-{sid}.pdf`. | FR-004, FR-006. |
| 5 | What does "convergence test" mean? | A post-implementation **spec↔code convergence report**: forward drift (spec→code) and reverse drift (code→spec). | Success Criteria, T029. |
| 6 | How strict is the workflow? | **Hard gate**, user may explicitly waive a step. | N/A (process). |
