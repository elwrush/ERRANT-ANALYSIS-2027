# Contract C-004: PDF Rendering

## Function Signature

```python
def render_technical_report(
    draft_path: Path,
    aggregated_data: AggregatedReportData,
    output_path: Path,
    template_path: Path = Path("templates/tech_report.html"),
) -> Path:
    """
    Render a signed-off Markdown draft into a PDF using Jinja2 + Playwright.

    The pipeline:
    1. Read the Markdown draft, split by `##` section headings
    2. Identify the References section: extract structured JSON reference
       entries from the JSON code fence (```json [...] ```)
    3. Convert each section's body from Markdown to HTML via markdown-it-py
       (CommonMark-compliant, no Pandoc dependency)
    4. Build TechReportTemplateContext with section HTML, structured
       references, and aggregated chart paths
    5. Render the Jinja2 HTML template
    6. Create output_path.parent if it does not exist
    7. Playwright converts HTML to A4 PDF
    8. Ghostscript flatten for print reliability

    Args:
        draft_path: Path to the signed-off Markdown draft.
        aggregated_data: Aggregated report data for charts and tables.
        output_path: Desired output PDF path. Parent dir created if absent.
        template_path: Path to the Jinja2 HTML template.

    Returns:
        Path to the generated PDF.

    Raises:
        FileNotFoundError: If draft_path or template_path do not exist.
        RuntimeError: If Playwright PDF generation fails.
    """
```

## Template Input Schema

```python
class ReferenceEntry(BaseModel):
    authors: str           # "Author, A. A., & Author, B. B."
    year: str              # "2020"
    title: str             # "Title of work"
    source: str            # "Journal Name, 12(3), 45-67" or "Publisher"
    doi: str = ""          # "https://doi.org/10.xxxx"

class TechReportTemplateContext(BaseModel):
    masthead_left: str    # Path to ACT.png (as file:// or data URI)
    masthead_center: str  # "C·E·L Mathayom"
    masthead_right: str   # Path to cambridge.png (as file:// or data URI)
    report_title: str
    generated_at: str     # Formatted date string
    sections: list[ReportSection]
    references: list[ReferenceEntry]
    appendix_tables: list[dict]
```

## PDF Output Contract

| Requirement | Check |
|-------------|-------|
| Paper size | A4 (595.28 × 841.89 pts) — verified with PyMuPDF |
| Margins | 1.6cm on all sides — via `@page` CSS |
| Masthead present | Text "C·E·L Mathayom" extractable from page 1 |
| Section headings | All 11 baseline headings extractable from full PDF |
| Charts embedded | At least 2 `<img>` tags rendered in PDF body |
| Grayscale only | Color count 0 (all RGB channels equal per test) |
| Page count | Auto — no fixed minimum; content-driven |

## CSS Paged Media Rules

```css
@page {
  size: A4;
  margin: 1.6cm;
}

@media print {
  .page-break { page-break-before: always; }
  .no-break { page-break-inside: avoid; }
}

.masthead {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
  text-align: center;
  margin-bottom: 0.3em;
}

.masthead img.left { height: 2.25cm; justify-self: start; }
.masthead img.right { height: 1.55cm; justify-self: end; }
.masthead h1 { font-size: 16pt; margin: 0; }

.separator { border: none; border-top: 1pt solid #000; margin: 0.3em 0; }

/* APA 7th hanging indent for reference list */
.reference-entry {
  padding-left: 1.5em;
  text-indent: -1.5em;
  margin-bottom: 0.5em;
  font-size: 10pt;
  line-height: 1.4;
}
.reference-entry .title { font-style: italic; }
```

## Contract Tests

| Test | Input | Expected |
|------|-------|----------|
| Full report with all sections | Complete draft (Markdown with headings, prose, JSON code fence references, chart refs) + full aggregated data | PDF with 11+ sections, all headings present, chart images embedded |
| Minimal data (1 student) | Draft + single-student data | PDF generated without errors, no chart images |
| APA references rendered correctly | Draft with `\`\`\`json [{...}]\`\`\` references section | PDF text extraction confirms author names, year, and DOI from reference entries |
| Markdown formatting preserved | Draft with **bold**, _italic_, tables, links | PDF renders bold/italic text, table borders visible, links present |
| Missing template | Draft + data, bad template_path | FileNotFoundError |
| Missing output directory | Draft + data + output_path in non-existent dir | PDF created successfully (parent dir auto-created) |
| Playwright unavailable | Any input | RuntimeError with install instructions |
| Page size A4 | Any output PDF | PyMuPDF confirms 595.28 × 841.89 pts |
