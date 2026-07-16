# C-007: Supabase `error_reports` insert/upsert

## Locations

- `errant_analysis.py:491` — `insert_error_reports()` (insert only)
- `batch_errant_upsert.py:226` — `upsert(batch, on_conflict="student_id,date")`

## Refactored Signature

```python
def upsert_error_counts(
    student_id: str,
    date: str,
    error_rate: int | None,
    error_counts: dict[str, int],
    summary: str = "",
    word_count: int = 0,
    class_label: str = "",
    name: str = "",
) -> bool
```

## Conflict Resolution

- On conflict `(student_id, date)`: update `error_percent`, all error count columns, `summary`
- Never overwrite `created_at` or `id`

## Error Count Columns

All columns from `ERROR_CODE_COLUMNS` (42 columns). Each mapped from ERRANT type via `ERRANT_CODE_TO_COLUMN`.

## Contract Tests

- `test_upsert_new_record` — verify insert
- `test_upsert_existing_record` — verify update on conflict
- `test_upsert_zero_counts` — all zero counts, non-null error_percent
- `test_upsert_supabase_unavailable` — graceful skip, logged warning
