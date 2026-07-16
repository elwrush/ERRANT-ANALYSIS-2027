# C-009: Playwright HTML → PDF

## Signature

```python
def html_to_pdf(
    html_content: str,
    output_path: Path,
    *,
    format: str = "A4",
    margin: dict | None = None,
    emulate_print: bool = True,
) -> Path
```

## Default Margin

```python
{
    "top": "1.5cm",
    "bottom": "1.5cm",
    "left": "1.5cm",
    "right": "1.5cm",
}
```

## Pipeline

1. `playwright.sync_api.sync_playwright()` as context manager
2. `browser.chromium.launch(headless=True)`
3. `browser.new_page(viewport={"width": 1240, "height": 1754})` — A4 at 96dpi
4. `page.set_content(html_content, wait_until="networkidle")`
5. If `emulate_print`: `page.emulate_media(media="print")`
6. `page.pdf(...)` with specified format and margins
7. Close browser

## Font Handling

Inject `@font-face` rules for Roboto fonts. Resolve font paths from config:

```python
FONT_PATH = Path(os.environ.get("TINY_TEX_FONTS", "~/.tinytex/..."))
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Playwright not installed | `ImportError` with install instructions |
| Chromium not installed | Raise `RuntimeError("Chromium not found. Run: playwright install chromium")` |
| Font files missing | Log warning, fall back to system fonts |
| HTML rendering timeout | Increase timeout, retry once |

## Contract Tests

- `test_html_to_pdf_creates_file` — verify non-empty PDF exists
- `test_html_to_pdf_page_count` — verify correct number of pages
- `test_html_to_pdf_contains_text` — extract text from PDF, verify content
- `test_html_to_pdf_chromium_missing` — mock missing browser
