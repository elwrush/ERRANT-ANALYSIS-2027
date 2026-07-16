# Command: write-technical-report

## Usage
`/write-technical-report`

## What it does
Interactive workflow to generate a technical assessment report from pre-existing ERRANT analysis JSONs. Guides the user through: data location → report title → optional custom sections → Tavily rhetorical research → data validation → aggregation → grayscale charts → Markdown draft → human review → PDF generation with C·E·L Mathayom masthead.

## Flow

1. Ask user for: path to data directory, report title, whether additional sections are needed
2. If additional sections: list 11 baseline sections, prompt for rhetorical question + insertion point per custom section
3. Run Tavily search for rhetorical best practices
4. Call `python src/technical_report_writer.py validate <path>` to check input JSONs
5. Call `python src/technical_report_writer.py aggregate <path>` to get aggregated statistics
6. Call `python src/technical_report_writer.py charts <path> <output_dir>` to generate grayscale-safe charts
7. Compose Markdown draft with all sections, inline citations with page/para numbers, APA 7th references as JSON code fence
8. Annotate each cited source PDF via PyMuPDF: yellow highlight + sticky note with report section, save to `references/annotated/`
9. Generate `references/citation-map.md` mapping citations to source files and pages
10. Write draft to `outputs/drafts/<title-slug>.md`
11. Present draft + citation map + annotated PDFs to user for review
12. Wait for explicit sign-off ("proceed", "generate", "sign off") or cancellation
13. On sign-off: call `python src/technical_report_writer.py render <draft> <output.pdf>` to produce final PDF
14. On cancel: save draft with "DRAFT — not signed off" suffix

## Dependencies

- Python 3.14
- `src/technical_report_writer.py` — validate, aggregate, charts, render subcommands
- `templates/tech_report.html` — Jinja2 template with C·E·L Mathayom masthead
- `images/ACT.png`, `images/cambridge.png` — school logos
- `outputs/drafts/` — Markdown draft output directory
- `references/annotated/` — annotated source PDFs
