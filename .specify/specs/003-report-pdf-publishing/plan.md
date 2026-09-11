# Report PDF Publishing — Implementation Plan

## Tech Stack Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transparency removal | Pillow composite RGBA/LA/P → RGB PNG | `pillow>=10.0` already a dependency; no new package. Pre-rendered opaque bytes mean Chromium embeds no soft mask. |
| Chart format | Keep Matplotlib **SVG**, alpha-free | Preserves vector crispness; only transparency is `axhspan(alpha=0.18)` in `generate_report.py:167`. |
| PDF rendering | Playwright Chromium (unchanged) | Already used by both pipelines; produces A4 paged output. |
| Ghostscript | Removed entirely | Delete `_flatten_pdf` and the `subprocess` gs block; drop `gs` from prerequisites. |
| Per-student output | One PDF per student, no padding/merge | Removes `_pad_and_merge_pdfs`; padding existed only to align booklets. |
| Shared helper | New `src/image_utils.py` | Single source of truth for opaque data-URI encoding used by both modules. |
| Lint / test | `ruff check src/ tests/`, `pytest tests/ -v` | Project standard. |

## Project Structure (touched files)

```
ERRANT-ANALYSIS/
├── src/
│   ├── image_utils.py               # NEW: opaque_png_bytes(), opaque_data_uri()
│   ├── generate_report.py           # MOD: opaque logos, alpha-free chart, drop merge+gs
│   └── technical_report_writer.py   # MOD: opaque logos, drop gs flatten
├── templates/
│   └── tech_report.html             # MOD: strip inline-SVG opacity (22 hits)
├── tests/
│   ├── test_image_utils.py          # NEW
│   ├── test_report.py               # MOD: chart/SVG assertions, opaque-image test, no-gs guard
│   └── test_technical_report_writer.py  # MOD: SVG-text grayscale test
├── .opencode/skills/local-report/SKILL.md   # MOD
├── .opencode/command/local-report.md        # MOD
└── AGENTS.md                        # MOD
```

## Architecture Overview

**Before:** render N PDFs → pad each to a 4-page multiple → concatenate → delete individuals → Ghostscript flatten → one collated file (RGBA logos + translucent SVG embedded throughout).

**After:** opaque logos → alpha-free chart SVG → render N PDFs → keep N standalone files. No concatenation, no padding, no Ghostscript.

## Component Breakdown

### 1. `src/image_utils.py` (new)
- `opaque_png_bytes(path: Path) -> bytes` — open with PIL; if mode `RGBA`/`LA`/`P`-with-transparency, `convert("RGBA")` and composite over an opaque white `Image.new("RGB", size, "white")`; else `convert("RGB")`; save to `BytesIO` as PNG. Always returns RGB (no alpha).
- `opaque_data_uri(path: Path) -> str` — `data:image/png;base64,...` from the above.
- Missing file raises `FileNotFoundError`; callers keep existing existence handling.

### 2. `src/generate_report.py`
- `_file_to_data_uri` (line 55) → delegate to `image_utils.opaque_data_uri`; drop the now-unused `mimetypes` import.
- `generate_chart` (line 140) → replace `axhspan(..., facecolor="#cccccc", alpha=0.18)` with the pre-blended opaque `#f6f6f6` (0.18·#cccccc over white), and make the background explicit: `fig.patch.set_facecolor("white")`, `fig.savefig(..., transparent=False, facecolor="white")`.
- Delete `_pad_and_merge_pdfs` (319–331) and `_flatten_pdf` (334–359).
- `main` (425–440) → remove the merge/delete/flatten block; keep individual PDFs; replace the "Merged/Flattened" prints with a single-file summary. Filename stays `{today}-{run_time}-{safe_class}-{sid}.pdf`.

### 3. `src/technical_report_writer.py`
- `_img_b64` (494–503) → delegate to `image_utils.opaque_data_uri` (return `""` when the file is absent).
- Delete the gs flatten block (547–558) and the `subprocess` import (line 2) if unused elsewhere.
- Add `transparent=False, facecolor="white"` to the four `savefig` calls (341, 363, 379, 415) as a guarantee (they are already alpha-free).

### 4. `templates/tech_report.html` (default template — 22 opacity hits)
- Pre-blend each `opacity` / `stroke-opacity` / `fill-opacity` against white so appearance is preserved: `#b0b0b0` @0.3 → `#e7e7e7`; `#000000` @0.6 → `#666666`; @0.4 → `#999999`; `<g opacity="0.7">` glyph fill → `#4d4d4d`; `#ffffff` @0.8 → `#ffffff`.
- `report.html` and `m2_3b_report.html` are already clean (0 hits) — no change.

### 5. Docs
- `local-report/SKILL.md`: fix frontmatter description, remove "Interleaved merge (always)" and "Ghostscript flattening" sections, update Output/compatibility.
- `.opencode/command/local-report.md`: replace "interleaved multi-student merge" and "interleaved output PDF path".
- `AGENTS.md`: rewrite the `_pad_and_merge_pdfs` / Ghostscript gotcha.

### 6. Tests
- New `tests/test_image_utils.py`: RGBA/LA/P inputs → decoded output is RGB with no alpha; opaque input round-trips.
- `tests/test_report.py`: keep `test_generate_chart_creates_svg`; add assertions that the SVG text contains no `opacity:` and includes a `#ffffff` background. Add a static guard that `generate_report`/`technical_report_writer` contain no `pdfwrite`/`"gs"`/`subprocess` call.
- `tests/test_technical_report_writer.py`: repoint `test_charts_grayscale` to parse SVG text (grayscale hex + no opacity attrs).

## Implementation Phases

1. **Phase 1 — helper (TDD):** `tests/test_image_utils.py`, then `src/image_utils.py` to green.
2. **Phase 2 — per-student pipeline:** wire helper, remove merge/flatten/padding, alpha-free chart, update prints.
3. **Phase 3 — technical report pipeline:** wire helper, remove gs block, explicit opaque savefig.
4. **Phase 4 — template:** strip the 22 inline-SVG opacity values in `tech_report.html`.
5. **Phase 5 — docs, tests, verification:** doc edits, new/updated tests, `ruff`, `pytest`, PDF object scan.

## Spec Traceability (pre-implementation drift check)

| FR | Plan coverage |
|----|---------------|
| FR-001 no Ghostscript | Phases 2, 3 |
| FR-002 opaque raster images | Phase 1 |
| FR-003 alpha-free charts | Phase 2 (`generate_report`), Phase 4 (`tech_report.html`) |
| FR-004 single-file output | Phase 2 |
| FR-005 retain individuals | Phase 2 |
| FR-006 naming unchanged | Phase 2 |
| FR-007 console output | Phase 2 |
| FR-008 docs | Phase 5 |
| FR-009 tests | Phases 1, 5 |

No forward drift found. Reverse-drift note: `templates/tech_report.html` inline-SVG opacity was implied by "alpha-free charts" but not named in the original spec; it is now folded into FR-003.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Pre-blended colours change appearance | Compute exact over-white blends; visually diff before/after PDFs. |
| Chromium still emits a transparency group despite opaque content | Verification step: scan output PDFs for `/SMask` and transparent `/Group`. |
| Removing 4-page padding changes page counts | Expected; captured in success criteria. |
| `tech_report.html` is hard-coded (ignores draft sections) | Scope limited to opacity only; no structural template change. |
| Pre-existing test failures | `test_charts_grayscale` fixed; other known failures untouched. |

## Dependencies

- No new packages (Pillow present). Ghostscript removed as a prerequisite. `PyMuPDF` remains (annotations in `technical_report_writer.py`); `generate_report.py` no longer imports it.
