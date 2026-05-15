# Skill: errant-analysis

## Purpose

Take transcribed student essay JSONs (output from `ingest-images`), generate a grammatically corrected version using a cloud AI model, run ERRANT to classify each correction by error type, and produce a structured JSON report with error counts, examples, markup, and error rate.

## Files

| Item | Path |
|------|------|
| Script | `src/errant_analysis.py` |
| Tests | `tests/test_errant.py` |
| Fixtures | `tests/fixtures/error_golden.json` |

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Input

Select one of the JSON files from `outputs/`. These are produced by the `ingest-images` skill and contain `student_id` and `student_text`.

## Output

Saved to `local-working/{folder}-{student_id}.json`:

```json
{
  "student_id": "12345",
  "original_text": "...",
  "corrected_text": "...",
  "sentence_pairs": [],
  "errant_analysis": {
    "errors": [],
    "uncategorised": []
  },
  "corrected_with_markup": "...",
  "error_rate": 30
}
```

## Configuration

| Config | Value |
|--------|-------|
| Provider | OpenRouter |
| Correction model | `mistralai/mistral-small-3.2-24b-instruct` |
| Input price | $0.075 / 1M tokens |
| Output price | $0.20 / 1M tokens |
| Temperature | 0.1 (low for deterministic corrections) |
| Context guard | 32K tokens |
| Rate limiting | exponential backoff (2^n + jitter) on errors |
| Jitter | 0.5–1.5s between API calls |
| API key | `OPENROUTER_API_KEY` in `.env` or environment |

## Cost estimate

A 500-word essay (~700 tokens) costs roughly $0.0002 — **320 essays for ~$0.02**, 10,000 essays for under $1.

## ERRANT uncategorised handling

The script includes a `post_classify_other` function that reclassifies ERRANT's OTHER results:
- Spelling (high Levenshtein similarity > 0.55)
- Orthography (case/whitespace only)
- Morphology (shared prefix)
- Determiner/article changes
- Preposition changes

## Codebase research via gh

If ERRANT produces unexpected output, use `gh api` to inspect the live upstream source — no clone needed:

```bash
# List ERRANT source tree
gh api repos/chrisjbryant/errant/contents/errant/en

# View classifier source (classification rules)
gh api repos/chrisjbryant/errant/contents/errant/en/classifier.py | jq -r .content | base64 -d

# View merger source (edit merging logic)
gh api repos/chrisjbryant/errant/contents/errant/en/merger.py | jq -r .content | base64 -d

# View latest commits touching a file
gh api repos/chrisjbryant/errant/commits?path=errant/en/classifier.py | jq '.[].commit.message'
```

Research from actual source — never hallucinate fixes.
