# Research: Library Compatibility & Version Guidance

## Python 3.14

- **Status**: Stable release for months (per spec clarification)
- **Key changes from 3.13**: PEP 649 (deferred evaluation of annotations) still deferred; PEP 696 (type parameter defaults) stabilised; `@dataclass(slots=True)` default behaviour; `pathlib.Path` methods accept `pathlib.Path` objects consistently
- **Impact**: All pip-installable packages with binary wheels must publish 3.14 wheels. Verify below.

## ERRANT (`errant>=3.0.0`)

| Item | Detail |
|------|--------|
| **Source** | `github.com/chrisjbryant/errant` |
| **PyPI** | `errant` package, last stable release per requirements.txt is >=3.0.0 |
| **Python 3.14** | Verify: `pip download errant --only-binary=:all:` for 3.14 wheel. If unavailable, may need `--no-binary errant` and build from source (requires C compiler for spaCy Cython extensions). |
| **Dependencies** | Requires spaCy >=3.7. The spaCy→thinc→Cython dependency chain is the main compatibility risk. |
| **Usage in project** | `errant.load("en")`, `annotator.parse()`, `annotator.annotate()` — no version-specific API changes expected. |

## spaCy (`spacy>=3.7`)

| Item | Detail |
|------|--------|
| **PyPI** | `spacy` package, >=3.7 |
| **Python 3.14** | Check `pip index versions spacy` for 3.14-compatible release. spaCy 3.8+ may be required. |
| **Model** | `en_core_web_sm` — verify `python -m spacy download en_core_web_sm` succeeds on 3.14 |
| **Vulnerability** | spaCy has had no critical CVEs in last 12 months (checked via pip-audit scope). |
| **Notes** | The `spacy-transformers` extension is NOT used; the project only uses `en_core_web_sm` for tokenization/sentence segmentation. |

## Playwright Python

| Item | Detail |
|------|--------|
| **PyPI** | `playwright` package |
| **Install** | `pip install playwright && playwright install chromium` |
| **Python 3.14** | Playwright Python installs a bundled Chromium. Verify wheel availability. |
| **PDF API** | `page.pdf(path="output.pdf", format="A4", margin={"top": "1.5cm", "bottom": "1.5cm", "left": "1.5cm", "right": "1.5cm"})` |
| **CSS Print** | `page.emulate_media(media="print")` before `page.pdf()` to activate `@media print` CSS rules |
| **Font loading** | Use `page.add_style_tag(content="...")` to inject @font-face rules for Roboto fonts from the TinyTeX installation. Alternatively, system fonts work if Chromium can find them. |

## Jinja2

| Item | Detail |
|------|--------|
| **PyPI** | `Jinja2` package |
| **Python 3.14** | No binary dependency — pure Python. Will work on 3.14. |
| **Usage** | Render HTML templates with student data, then pass rendered HTML to Playwright for PDF generation. |
| **Template inheritance** | Use base template for masthead, student-specific blocks per report. |

## Pydantic (`pydantic>=2.x`)

| Item | Detail |
|------|--------|
| **PyPI** | `pydantic` package, >=2.0 recommended for current ecosystem |
| **Python 3.14** | pydantic-core (Rust) wheels must exist. Verify `pip install pydantic` on 3.14. |
| **Usage** | `BaseModel` subclasses for every JSON shape written to disk. Use `field_validator` decorators for domain constraints. |
| **Performance** | pydantic v2 is 5-50x faster than v1 due to Rust core — important for 600+ JSON files in batch operations. |

## pandas (`pandas>=2.0`), Matplotlib, scipy

| Package | Python 3.14 | Notes |
|---------|------------|-------|
| pandas >=2.0 | Verify wheel | Used in `interpret_results.py`, `desk_statistics.py` |
| matplotlib >=3.9 | Verify wheel | Used for chart generation in `generate_report.py` |
| scipy >=1.11 | Verify wheel | Used in `desk_statistics.py` for Mann-Whitney U |
| pyarrow >=10.0 | Verify wheel | Used for Parquet I/O in `interpret_results.py` |

## Supabase Python Client

| Item | Detail |
|------|--------|
| **PyPI** | `supabase` package, installed |
| **Python 3.14** | Pure Python client with httpx dependency. Should work. |
| **Usage** | Query classlists, insert/upsert error_reports. No planned API changes. |

## pypdf (optional fallback)

| Item | Detail |
|------|--------|
| **PyPI** | `pypdf` package |
| **Usage** | Currently used in `generate_report.py` as fallback for PDF concatenation. Will be replaced by Playwright. |

## Key Risks

| Risk | Mitigation |
|------|------------|
| errant or spaCy lacks 3.14 wheel | Build from source: `pip install spacy --no-binary spacy,thinc,cymem,preshed,murmurhash` |
| Playwright Chromium incompatible with Linux/WSL | Use `playwright install chromium` with `--with-deps` flag |
| Font rendering differs between Typst and Playwright | Use `@font-face` with same Roboto OTFs from TinyTeX; render same HTML in Playwright headless screenshot for visual diff |
| LLM response_format not supported by OpenRouter | OpenRouter passes through DeepSeek's API. DeepSeek supports `response_format` on non-thinking models. Test with `disable_thinking=True`. |
| Existing `.typ` files mixed with new `.html`/`.pdf` files in outputs/ | Use separate output subdirectories: `outputs/typst/` (legacy) and `outputs/playwright/` (new) |
