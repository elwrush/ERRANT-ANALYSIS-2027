# C-005: `generate_report` → PDF

## Legacy Signature (to be replaced)

```python
# Current: Typst compilation path
subprocess.run(["typst", "compile", "--root", ".", str(typ_path), str(pdf_path)], ...)
```

## New Signature (Jinja2 → Playwright)

```python
from playwright.sync_api import sync_playwright

def render_report(
    student: dict,          # ReportData-compatible dict
    template_path: Path,    # Jinja2 template .html file
    output_path: Path,      # Target .pdf path
) -> Path
```

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student` | `dict` | Yes | ReportData fields |
| `template_path` | `Path` | Yes | Path to Jinja2 HTML template |
| `output_path` | `Path` | Yes | Where to write the PDF |

## Pipeline

1. Load Jinja2 template from `template_path`
2. Render template with `student` data → HTML string
3. Launch Playwright (headless Chromium)
4. Navigate to rendered HTML via `page.set_content(html)`
5. Set `page.emulate_media(media="print")`
6. Call `page.pdf(path=output_path, format="A4", margin={...})`
7. Close browser

## Output

| Condition | Return |
|-----------|--------|
| Success | `Path` to generated PDF |
| Template missing | Raises `FileNotFoundError` |
| Playwright missing | Raises `ImportError` with install instruction |

## Contract Tests

- `test_render_report_creates_pdf` — verify file exists
- `test_render_report_pixel_match` — compare vs Typst baseline using pixelmatch
- `test_render_report_missing_template` — FileNotFoundError
- `test_render_report_all_student_fields` — verify PDF text content
