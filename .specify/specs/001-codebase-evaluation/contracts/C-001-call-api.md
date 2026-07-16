# C-001: `_call_api` — LLM invocation

## Location

`errant_analysis.py:177` (existing), will be refactored into a shared utility.

## Signature

```python
def call_api(
    content: str,
    temperature: float = 0.6,
    model: str | None = None,
    *,
    disable_thinking: bool = True,
    response_format: dict | None = {"type": "json_object"},
) -> str | None
```

## Input

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | `str` | Yes | — | System prompt content |
| `temperature` | `float` | No | `0.6` | LLM temperature |
| `model` | `str\|None` | No | `None` (uses config default) | Model override |
| `disable_thinking` | `bool` | No | `True` | Disable thinking mode so temperature is respected |
| `response_format` | `dict\|None` | No | `{"type": "json_object"}` | JSON mode enforcement |

## Output

| Condition | Return |
|-----------|--------|
| Success | `str` — trimmed response text |
| API error (retryable) | raises `RetryableError` |
| Auth failure | raises `NonRetryableError` |
| Empty response | raises `RetryableError` |

## Side Effects

- Logs to `tqdm.write()` for batch progress
- Updates `extra_body` for thinking mode control

## Contract Tests

- `test_api_returns_trimmed_response` — mock response, verify stripped
- `test_api_disables_thinking_by_default` — verify `thinking.type` in `extra_body`
- `test_api_retries_on_rate_limit` — mock 3 failures, verify 3 retries
- `test_api_uses_response_format` — verify `response_format` in payload
- `test_api_auth_failure_returns_none` — mock `AuthenticationError`
