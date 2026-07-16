# Data Model — Technical Report Writer

## Entities

### ReportSession
Represents one interactive report generation workflow instance.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `data_path` | Path | Directory containing ERRANT analysis JSONs | Must exist, must contain ≥1 `.json` file |
| `title` | str | Report title | Non-empty, sanitized for filename safety |
| `additional_sections` | list[CustomSection] | User-requested custom sections | Max 5 sections; insertion point must be valid index |
| `status` | enum | `drafting`, `review`, `signed_off`, `cancelled` | — |
| `draft_path` | Path | Path to the Markdown draft file | Set when draft is written |
| `pdf_path` | Path | Path to the final PDF | Set when PDF is rendered |
| `created_at` | datetime | Session creation timestamp | — |

### CustomSection
A user-requested additional report section.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `rhetorical_question` | str | Section heading as a question | Must end with `?` |
| `insert_after` | int | 0-based index of baseline section to insert after | Must be 0–10 (11 baseline sections) |

### AggregatedReportData
Computed statistics from all student JSONs. This is the core data passed to the Jinja2 template.

| Field | Type | Description |
|-------|------|-------------|
| `meta` | ReportMeta | Report-level metadata (title, date, etc.) |
| `students` | list[StudentSummary] | Per-student summary data |
| `error_code_summary` | list[ErrorCodeBucket] | Error counts aggregated by ERRANT code |
| `cohort_summary` | list[CohortBucket] | Per-cohort error rate statistics |
| `overall_stats` | OverallStats | Global statistics across all students |
| `charts` | list[ChartRef] | Paths to generated chart images |

### ReportMeta

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Report title |
| `generated_at` | str | ISO timestamp |
| `n_students` | int | Number of students in dataset |
| `n_classes` | int | Number of unique classes |
| `cohorts` | list[str] | Unique cohort identifiers (e.g. ["M2", "M3"]) |
| `date_range` | tuple[str, str] | Min/max submission dates |

### StudentSummary

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | str | 5-digit ID |
| `name` | str | Student name |
| `class_` | str | Class code |
| `word_count` | int | Word count |
| `error_rate` | int | Error rate percentage |
| `cefr_level` | str | Inferred CEFR level (B1/B2) |
| `error_count` | int | Total errors |
| `top_errors` | list[ErrorCodeBucket] | Top 3 error codes for this student |

### ErrorCodeBucket

| Field | Type | Description |
|-------|------|-------------|
| `code` | str | ERRANT code (e.g. "R:VERB:TENSE") |
| `supercategory` | str | R/M/U prefix |
| `name` | str | Human-readable name from ERRANT_CODE_NAMES |
| `count` | int | Number of errors |
| `percentage` | float | Percentage of total errors |

### CohortBucket

| Field | Type | Description |
|-------|------|-------------|
| `cohort` | str | Cohort identifier |
| `n_students` | int | Number of students |
| `mean_error_rate` | float | Mean error rate |
| `median_error_rate` | float | Median error rate |
| `std_error_rate` | float | Standard deviation |
| `min_error_rate` | float | Minimum error rate |
| `max_error_rate` | float | Maximum error rate |

### OverallStats

| Field | Type | Description |
|-------|------|-------------|
| `n_students` | int | Total students |
| `mean_error_rate` | float | Mean error rate |
| `median_error_rate` | float | Median error rate |
| `std_error_rate` | float | Standard deviation |
| `min_error_rate` | float | Minimum |
| `max_error_rate` | float | Maximum |
| `mean_word_count` | float | Mean word count |
| `b1_count` | int | Students at B1 level |
| `b2_count` | int | Students at B2 level |

### ChartRef

| Field | Type | Description |
|-------|------|-------------|
| `section` | str | Which section this chart belongs to |
| `path` | Path | Absolute path to the chart image |
| `caption` | str | Figure caption |
| `type` | str | `bar` / `grouped_bar` / `histogram` / `line` |

### ReportSection (Jinja2 context)
Each report section is represented as a dict passed to the template:

```python
{
    "id": "introduction",              # kebab-case section ID
    "title": "Introduction",           # Section heading
    "rhetorical_question": None,       # Optional custom question
    "body": "<p>...</p>",             # HTML body content (from Markdown draft)
    "charts": [ChartRef, ...],        # Charts to embed in this section
    "tables": [dict, ...],            # Data tables for appendix
    "is_baseline": True,              # Whether this is a standard section
}
```

## Validation Rules

### Input JSON validation
- Each JSON file must pass `ErrantOutput.model_validate(data)`
- Files that fail validation are logged with specific field errors
- User can choose: skip failing files or abort

### Aggregation rules
- `class_` prefix (`M2`, `M3`, `M4+`) determines cohort for CEFR inference
- Error rate = `error_rate` field (already computed, 0–100)
- Error codes aggregated by supercategory (R/M/U prefix) for top-level, by full code for detail
- Students with `word_count < 40` flagged but included (their error_rate is None)

### File naming
- Draft: `outputs/drafts/<title-slug>.md` where title-slug = lowercase, hyphens for spaces, alphanumeric only
- PDF: `<title-slug>-tech-report.pdf` in the output directory chosen by user
- Chart images: `<output_dir>/charts/<section>-<type>.png`
