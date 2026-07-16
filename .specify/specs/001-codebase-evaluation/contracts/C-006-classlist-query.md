# C-006: Supabase `classlists` query

## Locations

- `ingest.py:65` — `lookup_student_info()`
- `errant_analysis.py:316` — `lookup_student_info()`
- `rename_json_files.py:24` — `check_student_exists()`

## Refactored Signature (in `src/config.py` or `src/supabase_utils.py`)

```python
def query_classlist(
    student_id: str | None = None,
) -> dict[str, dict[str, str]] | dict[str, str] | None
```

## Behavior

| Call Pattern | Return |
|--------------|--------|
| `query_classlist("12345")` | `{"name": "...", "class": "..."}` or `{}` if not found |
| `query_classlist()` | `{"12345": {"name": "...", "class": "..."}, ...}` — full cache |

## Caching

- Module-level dict cache (existing pattern in `ingest.py:77`)
- Cache invalidated on Supabase schema changes (manual, no webhook)

## Contract Tests

- `test_query_classlist_found` — mock Supabase row, verify name+class
- `test_query_classlist_not_found` — empty response, verify empty dict
- `test_query_classlist_caches` — second call uses cache, no Supabase query
- `test_query_classlist_connection_error` — Supabase unavailable, verify empty dict + logged warning
