# AGENTS.md — ERRANT-ANALYSIS

Pipeline: Supabase `error_reports` table → `technical_report_writer.py` (Jinja2 → Playwright) → A4 PDF report.

## Commands

```bash
ruff check src/ tests/
pytest tests/ -v
python src/technical_report_writer.py render <draft.md> <output.pdf>
python src/generate_report.py <folder>     # generates per-student PDFs in PDF/<folder>/
```

## Key scripts & data flow

| Script | What it does | Input | Output |
|--------|-------------|-------|--------|
| `src/technical_report_writer.py` | Main report PDF from Markdown draft + `local-working/` JSONs | Draft `.md` + `local-working/*.json` | Technical assessment PDF |
| `src/generate_report.py` | Per-student feedback report PDFs | `local-working/*.json` + Supabase `error_reports` historical data | `PDF/{class}/` PDF files |
| `src/errant_analysis.py` | Run ERRANT on transcribed JSONs | Ingestion JSONs | `local-working/` JSONs with `errant_analysis` field |
| `src/batch_errant_upsert.py` | Load pipeline results into Supabase | `local-working/` JSONs | Upserts to `error_reports` table |
| `src/config.py` | Shared constants: `B1_TARGET=19`, `B2_TARGET=15`, ERRANT code names, API keys | — | — |

## Critical rules

1. **Two-pass architecture**: grading pass (`technical_report_writer.py`, examiner prose) → student feedback (`generate_report.py`, warm HTML/underlines). Never merge.
2. **Student report benchmarks**: The benchmark lines in student PDFs use `B1_TARGET=19` and `B2_TARGET=15` from `config.py`. These are NOT CEFR-mandated — they are based on Štulrajterová (2023) observed rates.
3. **`generate_report.py` chart fix**: Use `chart_path.as_uri()` for Playwright `set_content()` — bare POSIX paths won't load. Base64 data URIs also work.
4. **`technical_report_writer.py` footer**: `footer_template` (snake_case) not `footerTemplate`.
5. **Playwright page number footer**: `display_header_footer=True` with `footer_template='<span class="pageNumber"></span>'`.

## Historical data for charts

`fetch_historical_data()` in `generate_report.py` queries Supabase `error_reports` first, falls back to `local-working/historical_data.json`. Create this file via `supabase db query --linked "SELECT student_id, date, error_percent FROM error_reports WHERE error_percent IS NOT NULL ORDER BY student_id, date;"`.

## Data sources

- **`local-working/`**: Pipeline-run JSONs (latest batch, ~30-100 students). Used for findings tables, error type distribution, cohort means.
- **`error_reports` table (Supabase)**: Full historical data (1,006 records, 160 students, 52 dates across 2025-2027). Used for historical charts and longitudinal tracking.
- **References in `references/`**: Annotated PDFs at `references/annotated/`. Citation map at `references/citation-map.md`.

## CEFR benchmarks (empirical, not aspirational)

| Level | Observed error rate | Source |
|-------|-------------------|--------|
| B1 | ~19% | Štulrajterová (2023), Ch. 4, p. 78 |
| B2 | ~15% | Štulrajterová (2023), Ch. 5, pp. 90, 103, 110 |

These are MEAN OBSERVED rates from a Czech EFL learner corpus — not CEFR-published targets.

## Reference formatting

References use APA 7th edition with a `formatted` field in the draft JSON. The template renders `{{ ref.formatted | safe }}` (HTML allowed for `<em>`, `&amp;`). DOIs appear as plain text, not hyperlinks.

## PDF merging

When appending student reports (Appendix 2), the merge script:
1. Renders main report (11 pages without appendix)
2. Finds `"Appendix 2: Sample student feedback"` text in the PDF
3. Inserts the student PDF pages after that page
4. Saves to temp file, replaces original (PyMuPDF cannot `save()` to the same path)

## Key files

| File | Purpose |
|------|---------|
| `templates/tech_report.html` | Main report Jinja2 template (sections, tables, inline SVG charts) |
| `templates/report.html` | Individual student feedback report template |
| `outputs/drafts/` | Markdown drafts with reference JSON data parsed into `context.references` |
| `outputs/charts/` | Per-student error rate tracking charts (intermediate PNG, inlined as SVG in main report) |
| `PDF/` | Generated per-student feedback report PDFs by class |
| `images/ACT.png` , `images/cambridge.png` | Masthead logos (embedded as base64 in reports) |
