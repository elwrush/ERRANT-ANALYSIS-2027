# Skill: local-report

## Purpose

Generate a combined Typst booklet from all ERRANT analysis outputs. All students are compiled into a single PDF, each occupying 4 pages (with blank pages as padding). Contains personalised greeting, AI-generated summary with human-readable error descriptions, error-rate line chart with CEFR target lines, original writing with underlined corrections, and error breakdown table.

## Files

| Item | Path |
|------|------|
| Report script | `src/generate_report.py` |
| ERRANT + summary script | `src/errant_analysis.py` |
| Supabase setup | `src/setup_error_analysis.py` |
| Images | `images/ACT.png`, `images/cambridge.png` |

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set environment variables:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ESL_KEY` | Service role key |
| `SUPABASE_DB_URL` | Direct DB connection string (for `setup_error_analysis.py` only) |

## Supabase table

The `error_reports` table stores historical error data for charting:

Columns: `id`, `created_at`, `student_id`, `class`, `name`, `error_percent`, `summary`, plus **45 error code columns** (`r_spell`, `r_det`, `r_verb_tense`, `m_noun`, `u_punct`, etc.) — one per ERRANT code, `INTEGER DEFAULT 0`.

Table setup: `python src/setup_error_analysis.py` (run once after creating the table).

## Workflow

1. Run ERRANT analysis (`/local-errant-analysis`) — this also generates summaries and inserts into `error_reports`
2. Run `python src/generate_report.py [folder_name]`

## Output

- Typst source: `outputs/{folder}/{dd-mm-yy}-{class}-combined.typ`
- PDF: `PDF/{folder}/{dd-mm-yy}-{class}-combined.pdf`
- Charts: `outputs/charts/{student_id}.png` (one per student)

## Page structure

Each student occupies a multiple of 4 pages for booklet printing:

| Page | Content |
|------|---------|
| 1 | Masthead grid (ACT logo, Mathayom Program, Cambridge logo), separator line, title "Writing Accuracy Feedback Report", subhead `{name} - {id} - {class}`, personalised greeting (*Dear {name},*), AI-generated summary with guidance, target-rate boilerplate, error-rate line chart with CEFR target line + gray shading |
| 2+ | **Your Writing with Corrections** — corrected text with `#underline[]` markup showing all corrections, subhead left-aligned ("I scanned your writing for errors...") |
| (same page) | **Your Original Writing (Uncorrected)** — verbatim student text, no page break between corrected and original sections (separated by `#v(2em)`) |
| + | Blank pages to pad to the next multiple of 4 (via pad-to-four logic) |

## Pad-to-four (critical — do not modify without research)

Each student must occupy exactly 4 pages. Blank pages are appended using Typst's `page(body: [])` inside a `context` block with label anchor. The following confirmed-working implementation MUST be used:

```typst
#box(width: 0pt) <pad-anchor-{N}>
#context {
  let num = counter(page).at(label("pad-anchor-{N}")).first()
  for _ in range(calc.rem-euclid(4 - num, 4)) {
    page([])
  }
}
```

### Why this works (and why other approaches fail)

| Approach | Result | Root cause |
|----------|--------|------------|
| `pagebreak()` in a for loop | ❌ Consolidates to 3 pages | Consecutive `pagebreak()` at same context position merge |
| `h(0pt)` + `pagebreak()` | ❌ Still consolidates | `h(0pt)` is invisible, doesn't separate pagebreaks |
| `[]` + `pagebreak()` | ❌ Renders "[]" text + consolidates | `[]` in code mode = empty array = literal text |
| `[#[] <anchor>]` label | ❌ Renders "[]" text | `#[]` in markup evaluates to empty array |
| `while` loop with `pagebreak()` | ❌ Same consolidation | All pagebreaks still at one logical position |
| `page([])` | ✅ 4 pages | Creates actual page element — cannot consolidate |
| `#box(width: 0pt) <anchor>` | ✅ Invisible | Zero-width box produces no visible output |

### Key Typst rules learned

1. **`context { }` is code mode**: `[]` is an empty ARRAY, not empty content. It renders as literal `[]` text. Use `page([])` where `[]` is a function argument (safe) or `#box(width: 0pt)` for invisible anchors.

2. **`pagebreak()` consolidates**: Multiple consecutive `pagebreak()` calls at the same context location merge into one page break. Use `page([])` which creates a full page element that cannot merge.

3. **`body` is positional**: `page(body: [])` errors — use `page([])` (pass content as positional arg).

4. **`#[]` in markup is an array**: In `[#[] <label>]`, the `#` enters code mode and `[]` is an empty array. This may serialize as literal `[]`. Use `#box(width: 0pt) <label>` instead.

## Paragraph breaks

**Critical rule**: In Typst markup, a single `\n` is whitespace (collapsed to space). Only `\n\n` (blank line) creates a paragraph break.

The ERRANT `corrected_typst` field uses single `\n` between paragraphs. In `build_student_block()`, the newlines are doubled:
```python
marked = markup.replace("\n", "\n\n")
```

The original uncorrected text (`original_text` from the ERRANT JSON) is plain text, not Typst markup. It is escaped via `esc()` before being embedded, and `\n` is doubled to `\n\n` for Typst paragraph breaks:
```python
orig_escaped = esc(orig).replace("\n", "\n\n")
```

**Do NOT**:
- Leave `\n` unmodified → paragraphs merge into one
- Replace `\n` with space → same problem
- Use Typst `\` (backslash) for paragraph breaks → that's a line break, keeps same paragraph

This is the ONLY transformation applied to `corrected_typst` in `build_student_block()` — all `<u>` → `#underline[]` conversion has been eliminated since ERRANT now emits Typst-native syntax directly.

## Font

Base: Roboto 14pt body (scales to ~10pt readable in A5 booklet when A4 folded). Title: 16pt. Masthead text: 18pt. Top margin: 2.0cm.

## ERRANT error descriptions

ERRANT codes are converted to human-readable descriptions using a mapping derived from `errant/en/classifier.py`. Broadened descriptions cover classification edge cases:

| Code | Description |
|------|-------------|
| R:SPELL | "Spelling or capitalisation mistakes" (covers 'i'→'I' case changes that ERRANT misclassifies) |
| R:ORTH | "Capitalisation, spacing, or punctuation errors" (covers punctuation edits ERRANT tags as orthography) |

Summary uses the top 3 errors, ranked by frequency (descending `count`). Each error includes explicit guidance: *"It is better to write '[correction]'"*.

## Chart

- X-axis: dates formatted as "May 5", "Nov 6" (max 5 data points: 4 historical + current)
- Y-axis: error rate %
- CEFR target line: B1=12% (M3), B2=7% (M4+). Solid horizontal line with "Target (B1/B2)" label. Gray `axhspan` alpha=0.18 below the line

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No ERRANT outputs | Reports error, exits |
| No Supabase credentials | Runs charts without historical data (current point only) |
| No summary in JSON | Uses placeholder text |
| Typst compilation fails | Reports compilation error |
| Chart generation fails | Reports error, continues without chart |

## Dependencies

- `typst 0.14+` (CLI installed separately)
- `matplotlib>=3.9` (for charts)
