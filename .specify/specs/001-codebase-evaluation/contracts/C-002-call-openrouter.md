# C-002: `call_openrouter` — Vision API invocation

## Location

`ingest.py:250`

## Signature

```python
def call_openrouter(data_url: str) -> dict | None
```

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data_url` | `str` | Yes | Base64-encoded JPEG data URL (`data:image/jpeg;base64,...`) |

## Output

| Condition | Return |
|-----------|--------|
| Success | `dict` with `student_id` and `student_text` keys |
| JSON parse failure | `None` (after 3 attempts at extraction) |
| HTTP 429/502/503 | Raises `RetryableError` |

## Side Effects

- Prints warnings via `print()` if JSON cannot be parsed

## Contract Tests

- `test_openrouter_returns_valid_json` — mock valid response
- `test_openrouter_retries_on_429` — mock rate limit
- `test_openrouter_extracts_json_from_fence` — mock triple-backtick response
- `test_openrouter_no_key_returns_none` — unset API key
