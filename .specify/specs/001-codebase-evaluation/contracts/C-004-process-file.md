# C-004: `process_file` → output JSON

## Location

`errant_analysis.py:935`

## Signature

```python
def process_file(
    file_path: Path,
    nlp: spacy.Language | None = None,
    annotator: errant.Annotator | None = None,
) -> dict | None
```

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | `Path` | Yes | Path to IngestionOutput JSON |
| `nlp` | `spacy.Language\|None` | No | Lazy-load on None |
| `annotator` | `errant.Annotator\|None` | No | Lazy-load on None |

## Output

| Condition | Return |
|-----------|--------|
| Success | `dict` matching ErrantOutput model |
| Empty text | `None` |

## Side Effects

- Writes JSON to `local-working/{folder}-{record_id}.json`
- Inserts `error_reports` row into Supabase
- Generates LLM summary

## Contract Tests

- `test_process_file_empty_text_skips` — empty `student_text` returns None
- `test_process_file_identity_noop` — original==corrected, verify identity flag
- `test_process_file_has_all_top_keys` — verify output dict shape
- `test_process_file_write_to_disk` — verify file created in local-working
