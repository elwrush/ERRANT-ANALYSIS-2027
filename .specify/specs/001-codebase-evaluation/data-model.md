# Data Model

## Overview

Three principal data shapes flow through the pipeline. Each maps to a Pydantic `BaseModel` in `src/models.py`.

```
IngestionOutput  ──→  ErrantOutput  ──→  ReportData
(student_text)        (correction +         (chart + markup +
                       ERRANT analysis)      summary + metadata)
```

---

## 1. IngestionOutput

**File**: `outputs/{folder}/{student_id}.json`  
**Producer**: `src/ingest.py`  
**Consumer**: `src/errant_analysis.py`

| Field | Type | Required | Constraints | Source |
|-------|------|----------|-------------|--------|
| `student_id` | `str` | Yes | 5-digit numeric string | Vision model from first page |
| `student_text` | `str` | Yes | Non-empty; max 10000 chars | Transcribed handwriting |
| `word_count` | `int` | Yes | >= 1 | Computed from `student_text.split()` |
| `name` | `str` | No | Max 100 chars | Supabase classlist lookup |
| `class` | `str` | No | Max 20 chars | Supabase classlist lookup |
| `source_images` | `list[str]` | No | Max 10 filenames | Page filenames |

**Validation rules**:
- `student_id` must be 5 digits (`^\d{5}$`)
- `student_text` must not be empty
- `word_count` must equal `len(student_text.split())`
- If `name` is provided, `class` should also be provided (both from Supabase)
- `source_images` is informational only — not validated for existence

---

## 2. ErrantOutput

**File**: `local-working/{folder}-{record_id}.json`  
**Producer**: `src/errant_analysis.py`  
**Consumer**: `src/generate_report.py`, `src/rename_json_files.py` (reads student_id)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `student_id` | `str` | Yes | 5-digit |
| `original_text` | `str` | Yes | Non-empty |
| `corrected_text` | `str` | Yes | Non-empty |
| `sentence_pairs` | `list[dict]` | Yes | Each: `{"original": str, "corrected": str}` |
| `corrected_typst` | `str` | Yes | Typst/plain markup (legacy) |
| `error_rate` | `int\|None` | Yes | 0-100 or None (<40 words) |
| `word_count` | `int` | Yes | >= 1 |
| `name` | `str` | No | Max 100 chars |
| `class` | `str` | No | Max 20 chars |
| `record_id` | `str` | No | Composite key |
| `submission_date` | `str` | No | ISO date |
| `topic` | `str` | No | Max 200 chars |
| `summary` | `str` | No | Freed from LLM summary |
| `summary_data` | `dict\|None` | No | Structured LLM summary |
| `summary_type` | `str` | No | `"llm"`, `"empty"` |
| `date_created` | `str` | Yes | ISO date |
| `metadata` | `dict` | Yes | See Metadata sub-model |
| `errant_analysis` | `dict` | Yes | See ErrantAnalysis sub-model |

### ErrantAnalysis (sub-model)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `errors` | `list[dict]` | Yes | Each: `{"type": str, "count": int, "example": str, "context_original": str, "context_corrected": str}` |
| `uncategorised` | `list[dict]` | Yes | Each: `{"orig": str, "cor": str, "orig_start": int, "orig_end": int}` |
| `dropped_edits` | `dict` | Yes | With `UNK`, `U:SPACE` counts + example lists |

### Metadata (sub-model)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `model` | `str` | Yes | `"deepseek-v4-flash"` |
| `identity_check` | `bool` | Yes | |
| `overcorrection_count` | `int` | Yes | >= 0 |
| `overcorrection_warnings` | `list[dict]` | Yes | |
| `total_edit_count` | `int` | Yes | >= 0 |
| `edit_width_stats` | `dict` | Yes | `max_span`, `avg_span`, `multi_token_edits` |

---

## 3. ReportData

**File**: (generated programmatically, not written to disk directly)  
**Consumer**: Jinja2 template → Playwright PDF

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `student_id` | `str` | Yes | 5-digit |
| `name` | `str` | Yes | |
| `class` | `str` | Yes | |
| `word_count` | `int` | Yes | >= 1 |
| `error_rate` | `int\|None` | Yes | |
| `summary_praise` | `str` | No | Warm teacher voice text |
| `summary_rendered` | `str` | No | Structured error breakdown |
| `corrected_markup` | `str` | Yes | HTML with `<u>` tags for corrections |
| `original_text` | `str` | Yes | |
| `chart_path` | `str` | Yes | Relative path to PNG chart |
| `target_rate` | `int` | Yes | 7 (B2) or 12 (B1) |
| `cefr_level` | `str` | Yes | `"B1"` or `"B2"` |

---

## 4. ConfigModel (new — to be created)

**File**: `src/config.py`  
**Purpose**: Single source of truth for all shared constants

| Field | Type | Source |
|-------|------|--------|
| `api_keys` | `dict` | `os.environ.get()` |
| `model_names` | `dict[str, str]` | Hardcoded with env override |
| `paths` | `dict[Path, Path]` | `Path(__file__).parent` relative |
| `errant_code_to_column` | `dict[str, str]` | Moved from `errant_analysis.py` + `generate_report.py` |
| `errant_code_names` | `dict[str, str]` | Human-readable descriptions |
| `error_code_columns` | `list[str]` | Column name list |

**Methods**:
- `get_api_key(name: str) -> str` — load from env, raise if missing
- `resolve_path(key: str) -> Path` — absolute path resolution

---

## Entity-Relationship

```
        classlists (Supabase)
              │
              │ student_id
              ▼
  student_submissions (Supabase) ──→ error_reports (Supabase)
        │                                      │
        │ student_text                          │ error_percent, error counts
        ▼                                      ▼
  output JSONs (filesystem) ──→ ERRANT JSONs (filesystem) ──→ PDF reports
  (IngestionOutput)              (ErrantOutput)                 (ReportData)
```

No foreign key constraints exist in the filesystem pipeline — relationships are by `student_id` string matching.
