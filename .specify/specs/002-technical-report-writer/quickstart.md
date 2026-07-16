# Technical Report Writer — Quickstart

## Setup

```bash
# Ensure dependencies are installed
pip install -r requirements.txt
playwright install chromium

# Copy header images (if not already present)
# Images are already at images/ACT.png and images/cambridge.png
```

## Running

```bash
# Start the interactive report writing session
# Inside Kilo CLI:
/write-technical-report

# The agent will:
# 1. Ask for data directory path
# 2. Ask for report title
# 3. Ask for optional additional sections
# 4. Research rhetorical best practices (Tavily)
# 5. Validate & aggregate data
# 6. Generate charts
# 7. Compose Markdown draft
# 8. Present for human review
# 9. On sign-off: render final PDF
```

## Python Helper Subcommands

```bash
# Validate input JSONs
python src/technical_report_writer.py validate /path/to/data/

# Aggregate statistics
python src/technical_report_writer.py aggregate /path/to/data/

# Generate charts
python src/technical_report_writer.py charts /path/to/data/ /path/to/output/

# Render PDF from signed-off draft
python src/technical_report_writer.py render /path/to/draft.md /path/to/output.pdf
```

## Verification Scenarios

### Scenario 1: Basic report (single class)
```
Input:  /path/to/M2-class-json/
Title:  "M2 Class Writing Analysis"
Sections: (none additional)
Expected: PDF with all 11 baseline sections, charts, data appendix
```

### Scenario 2: Multi-class report with custom section
```
Input:  /path/to/all-classes-json/
Title:  "Q2 2026 Writing Analysis"
Sections:
  - "What strategies helped students improve most?" (insert after "How can teachers use this report?")
Expected: PDF with 12 sections, cohort comparison charts, custom section between classroom advice and ERRANT explanation
```

### Scenario 3: Empty/Invalid data directory
```
Input:  /path/to/empty-folder/
Expected: Error message "No JSON files found at <path>"
```

### Scenario 4: Mixed valid/invalid JSONs
```
Input:  /path/to/mixed-data/
Expected: Validation log with per-file errors, prompt to skip or abort
```

### Scenario 5: Single student data
```
Input:  /path/to/single-student/
Title:  "Individual Writing Analysis"
Expected: Summary table instead of cohort charts, note about limited data
```

## Test Commands

```bash
# Linting
ruff check src/technical_report_writer.py tests/test_technical_report_writer.py

# Tests
pytest tests/test_technical_report_writer.py -v

# Full test suite
pytest tests/ -v
```

## Output Inspection

```bash
# Check Markdown draft
cat outputs/drafts/my-report.md

# Check PDF generation
python src/technical_report_writer.py render outputs/drafts/my-report.pdf outputs/my-report.pdf

# Verify PDF page count
python -c "import fitz; doc=fitz.open('outputs/my-report.pdf'); print(f'{doc.page_count} pages')"

# Verify section headings in PDF
python -c "
import fitz
doc=fitz.open('outputs/my-report.pdf')
for page in doc:
    text=page.get_text()
    for section in ['Introduction','What are the most important findings','How was the report compiled','What does this report say','How can teachers use','What is involved','limitations of ERRANT','Future directions','Appendix','Technical details','References']:
        if section.lower() in text.lower():
            print(f'Found: {section}')
"
```
