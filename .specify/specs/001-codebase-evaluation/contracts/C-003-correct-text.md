# C-003: `correct_text` → ERRANT analysis

## Location

`errant_analysis.py:140`

## Signature

```python
def correct_text(
    original_text: str,
    nlp_model: spacy.Language,
) -> tuple[str, list, list]
```

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `original_text` | `str` | Yes | Student's original writing |
| `nlp_model` | `spacy.Language` | Yes | Loaded spaCy `en_core_web_sm` pipeline |

## Output

`tuple[str, list, list]`: `(corrected_full_text, [], [])`

| Element | Type | Description |
|---------|------|-------------|
| `corrected_full_text` | `str` | LLM-corrected version of original |
| `_` (index 1) | `list` | Always `[]` (per-sentence edit placeholder; not used) |
| `_` (index 2) | `list` | Always `[]` (reserved) |

## Downstream: ERRANT annotation

```python
annotator = errant.load("en")
orig_parse = annotator.parse(original_text)
cor_parse = annotator.parse(corrected_text)
edits = annotator.annotate(orig_parse, cor_parse)
```

## Contract Tests

- `test_correct_text_nonempty` — verify returns non-empty string
- `test_correct_text_preserves_paragraphs` — verify paragraph count match
- `test_correct_text_fluency_rewrite_retry` — mock fluency rewrite, verify retry
- `test_errant_detects_known_errors` — known fixture pairs produce expected types
- `test_errant_identity_no_edits` — identical texts produce 0 edits
