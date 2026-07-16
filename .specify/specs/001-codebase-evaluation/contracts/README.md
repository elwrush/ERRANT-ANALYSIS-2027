# Interface Contracts

## Conventions

- All LLM API calls use `response_format={"type": "json_object"}`
- All JSON write paths validate through `BaseModel.model_validate()` before writing
- All imports reference `src/config.py` for shared constants
- All scripts use `src/models.py` for data shape definitions

## Contract Index

| Contract | File | Type |
|----------|------|------|
| C-001 | `_call_api` | LLM invocation |
| C-002 | `call_openrouter` | Vision API invocation |
| C-003 | `correct_text` → `errant_analysis` | Correction → ERRANT |
| C-004 | `process_file` → output JSON | ERRANT processing |
| C-005 | `generate_report` → PDF | Report generation |
| C-006 | Supabase `classlists` query | Database read |
| C-007 | Supabase `error_reports` insert/upsert | Database write |
| C-008 | Jinja2 template → HTML | Template rendering |
| C-009 | Playwright HTML → PDF | PDF generation |
