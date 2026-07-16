# Technical Report Writer — Implementation Plan

## Tech Stack Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent orchestrator | Kilo (CLI) | The agent manages interaction, prose composition, Tavily research, and the human review gate. No Python→LLM calls needed for content. |
| HTML templating | Jinja2 | Already in use (`templates/report.html`). Consistent with project conventions and Article 5 of CONSTITUTION. |
| PDF rendering | Playwright (Chromium headless) | Already in use (`html_to_pdf()` in `generate_report.py`). Produces pixel-perfect A4 PDFs with CSS paged media support. |
| Charts | Matplotlib (Agg backend) | Already in use (`generate_chart()`). Must use grayscale-safe patterns (hatching, dots, stripes) — no color-only differentiation. |
| Data validation | Pydantic BaseModel | Already in use (`src/models.py`). Input JSONs validated against `ErrantOutput` model before aggregation. |
| Style research | Tavily search skill | Already configured (confirmed during clarify). Agent calls Tavily before composing prose. |
| Linguistic style | Agent LLM (response_format) | Agent writes in educated Australian teacher voice. Tavily rules applied to avoid "AI slop". |
| Linting | Ruff | Project standard (`ruff check src/ tests/`). |
| Testing | Pytest | Project standard (`pytest tests/ -v`). |

## Project Structure

```
ERRANT-ANALYSIS/
├── .kilo/
│   └── commands/
│       └── write-technical-report.md    # CLI command definition
├── src/
│   └── technical_report_writer.py       # Python helper: data aggregation, charts, PDF rendering
├── templates/
│   └── tech_report.html                 # Jinja2 template for the technical report
├── tests/
│   └── test_technical_report_writer.py  # Tests for report writer
├── images/
│   ├── ACT.png                          # Existing — school logo (left)
│   └── cambridge.png                    # Existing — Cambridge logo (right)
├── outputs/
│   └── drafts/                          # Markdown drafts before human review
└── references/
    ├── annotated/                       # Annotated source PDFs with highlights
    └── citation-map.md                  # Per-citation source mapping
```

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Kilo Agent (Orchestrator)              │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ User interact │  │ Tavily       │  │ Prose         │  │
│  │ (data path,   │→│ research     │→│ composition   │  │
│  │  title,       │  │ (rhetoric)   │  │ (agent LLM)   │  │
│  │  sections)    │  └──────────────┘  └───────┬───────┘  │
│  └──────┬───────┘                              │          │
│         │                                      │          │
│         ▼                                      ▼          │
│  ┌───────────────────────────────────────────────────┐   │
│  │        Python Helper (technical_report_writer.py)  │   │
│  │                                                    │   │
│  │  1. Load & validate JSONs (Pydantic)              │   │
│  │  2. Aggregate error statistics (per-code, per-     │   │
│  │     cohort, per-student)                           │   │
│  │  3. Generate grayscale-safe charts (Matplotlib)    │   │
│  │  4. Render Jinja2 → HTML                           │   │
│  │  5. Playwright HTML → PDF                          │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │              Human Review Gate                     │   │
│  │  Markdown draft → teacher reviews → sign-off → PDF│   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. CLI Command: `/write-technical-report`
- **File**: `.kilo/commands/write-technical-report.md`
- **Triggered by**: User typing `/write-technical-report` in Kilo
- **Flow**:
  1. Agent asks user for: data directory path, report title, optional additional sections (with insertion point)
   2. Agent runs Tavily research for rhetorical best practices
   3. Agent calls `technical_report_writer.py validate <path>` to check input JSONs
   4. Agent calls `technical_report_writer.py aggregate <path>` to get aggregated statistics
   5. Agent calls `technical_report_writer.py charts <path> <output_dir>` to generate grayscale charts
   6. Agent composes Markdown draft using agent LLM (educated Australian teacher voice), with inline citations including page/para numbers
   7. Agent annotates each cited source PDF: opens with PyMuPDF, highlights cited passages, adds sticky annotation with report section name and citation, saves to `references/annotated/<source>-annotated.pdf`
   8. Agent writes `references/citation-map.md` mapping each inline citation → source file, page number, and highlighted passage text
   9. Agent writes draft to `outputs/drafts/<title-slug>.md`
  10. Agent presents draft + citation map + annotated PDFs to user for review → waits for sign-off
  11. On sign-off: agent calls `technical_report_writer.py render <draft.md> <output.pdf>` to produce final PDF

### 2. Python Helper: `src/technical_report_writer.py`
- **Subcommands** (called as `python src/technical_report_writer.py <subcommand> [args]`):
  - `validate <path>` — validates all JSONs against `ErrantOutput` model; returns pass/fail with per-file errors
  - `aggregate <path>` — loads validated JSONs, computes:
    - Per-ERRANT-code error counts and percentages
    - Per-cohort error rate distribution
    - Per-student error rate with historical comparison (from Supabase or local working)
    - Total students, mean error rate, median, min/max
    - Cohort-level statistics
  - `charts <path> <output_dir>` — generates grayscale-safe charts:
    - ERRANT code frequency bar chart (horizontal, with hatching patterns)
    - Cohort comparison grouped bar chart (with dot/stripe patterns)
    - Error rate distribution histogram (if enough data points)
   - `render <draft_path> <output_path>` — renders final PDF:
    - Reads the signed-off Markdown draft
    - Parses the Markdown body into HTML using `markdown-it-py` (CommonMark-compliant, lightweight, no Pandoc dependency)
    - Splits the draft into sections by `##` headings, extracting the body HTML per section
    - Converts the References section: structured reference entries (author, year, title, source, DOI) are rendered by the Jinja2 template as styled HTML with CSS hanging indent
    - Injects section body HTML and structured reference data into the Jinja2 template (with C·E·L Mathayom masthead)
    - Playwright converts HTML to PDF
    - Ghostscript flatten (PDF transparency rendering)

### 3. Jinja2 Template: `templates/tech_report.html`
- **Layout**:
  - C·E·L Mathayom masthead (cambridge.png left, "C·E·L Mathayom" center, ACT.png right)
  - Separator line
  - Report title, date, metadata
  - Per-section rendering (each section is a Jinja2 block)
  - Charts embedded as `<img>` tags from local files
  - Tables for appendix data
  - References section (APA 7th)
- **Grayscale**: All CSS uses black/gray, no color hex values. Chart images use hatching patterns.

### 4. Markdown Draft
- The agent composes the Markdown draft with all 11 baseline sections (plus any custom sections)
- Format: standard GFM Markdown with `##` headings for sections
- Charts referenced as `![Chart description](relative/path.png)`
- Tables for data appendix
- Inline citations with page/paragraph numbers: `(Author, 2020, p. 42)`
- No HTML, no Typst, no emoji
- The References section heading MUST be followed by a Markdown code fence containing a JSON array of structured reference entries. This JSON is parsed by the `render` subcommand and rendered as styled HTML by the Jinja2 template.
- Reference entry format:
  ```json
  {"authors": "Author, A. A., & Author, B. B.", "year": "2020", "title": "Title of work", "source": "Journal Name, 12(3), 45-67", "doi": "https://doi.org/10.xxxx"}
  ```

### 6. Citation Management
- After composing the Markdown draft, the agent opens each cited source PDF with PyMuPDF (`fitz`)
- For each cited passage: highlights the text span in yellow, adds a sticky annotation on the highlight containing the report section name (e.g. "Section: What are the most important findings?")
- Saves annotated copy as `references/annotated/<base-name>-annotated.pdf`
- Generates `references/citation-map.md` with entries:
  ```markdown
  ## Section: What are the most important findings?
  - (Ellis, 2008, p. 72) → references/annotated/Ellis-2008-annotated.pdf, page 72
    > "Explicit instruction on grammatical structures leads to significant improvement..."
  ```
- Edge cases handled:
  - Scanned/image-only PDF → skip annotation, note in citation map
  - Permission-protected PDF → skip, note in citation map
  - Source PDF not found on disk → skip, note in citation map

### 5. Human Review Gate
- After draft written, agent presents path and summary to user
- User reviews the `.md` file, can request changes
- Agent can revise and re-present
- On sign-off, agent proceeds to PDF rendering
- If cancelled, draft saved with "DRAFT — not signed off" note

## Implementation Phases

### Phase 1: Foundation (Python helper)
- Create `src/technical_report_writer.py` with `validate`, `aggregate`, `charts` subcommands
- Write tests: `test_technical_report_writer.py`
- Red/green TDD for each subcommand

### Phase 2: Template
- Create `templates/tech_report.html` based on WRITING_ASSESSMENT_NEW cohort_report.html masthead
- Include C·E·L Mathayom branding with locally-copied logos (already exist in `images/`)
- All 11 sections as Jinja2 blocks
- Grayscale CSS

### Phase 3: Agent command & orchestration
- Create `.kilo/commands/write-technical-report.md` with the interactive workflow
- Wire up: Tavily research → data validation → aggregation → charts → Markdown draft → review gate → PDF render

### Phase 4: Integration & testing
- End-to-end test with real data
- Verify grayscale output, section headings, references, charts
- Lint: `ruff check src/ tests/`
- Test: `pytest tests/ -v`

## Dependencies

| Dependency | Source | Purpose |
|------------|--------|---------|
### Python packages (pip / requirements.txt)

| Package | Purpose |
|---------|---------|
| `jinja2` | HTML template rendering |
| `playwright` | PDF generation from HTML |
| `matplotlib` | Chart generation (Agg backend) |
| `pydantic` | Input JSON validation |
| `markdown-it-py` | Markdown→HTML conversion (no Pandoc) |
| `pytest` (dev) | Testing |
| `ruff` (dev) | Linting |

### Kilo skills (builtin, not pip)

| Skill | Purpose |
|-------|---------|
| Tavily search | Rhetorical research for prose style rules |
