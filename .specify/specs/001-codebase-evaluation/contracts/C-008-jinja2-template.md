# C-008: Jinja2 template → HTML

## Template Location

`templates/report.html` (new) — replaces `build_student_block()` in `generate_report.py`

## Template Variables (provided by Python renderer)

| Variable | Type | Description |
|----------|------|-------------|
| `student_id` | `str` | 5-digit ID |
| `name` | `str` | Student name |
| `class_label` | `str` | Class label |
| `word_count` | `int` | Word count |
| `error_rate` | `int\|None` | Error rate percentage |
| `cefr_level` | `str` | "B1" or "B2" |
| `target_rate` | `int` | 7 or 12 |
| `chart_path` | `str` | Path to chart PNG |
| `summary_praise` | `str` | Praise paragraph (HTML-safe) |
| `summary_errors` | `list[dict]` | Error breakdowns: `{"name": str, "explanation": str}` |
| `corrected_markup` | `str` | Corrected text with `<u>` tags |
| `original_text` | `str` | Raw original text (HTML-escaped) |
| `today` | `str` | Formatted date |
| `header_logo_left` | `str` | Path to ACT logo PNG |
| `header_logo_right` | `str` | Path to Cambridge logo PNG |

## CSS Requirements (via `<style>` tag in template)

- A4 page dimensions (`210mm x 297mm`)
- `@page { size: A4; margin: 1.5cm; }`
- `@media print { ... }` rules for page-break-after
- `.masthead` grid with logos left/center/right
- `.chart` centered, max 80% width
- `u` for corrections (underline style matching current Typst output)
- Roboto font family via `@font-face` from TinyTeX path

## Contract Tests

- `test_template_renders_all_variables` — render with all vars, verify output contains each
- `test_template_handles_none_error_rate` — short-text case
- `test_template_generates_print_css` — verify `@page` rule in rendered output
- `test_template_empty_summary` — verify renders without praise/errors
