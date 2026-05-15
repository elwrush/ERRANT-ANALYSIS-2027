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
  "error_rate": 30,
  "metadata": {
    "model": "mistralai/mistral-small-3.2-24b-instruct",
    "temperature": 0.1,
    "identity_check": false,
    "overcorrection_count": 0,
    "overcorrection_warnings": [],
    "total_edit_count": 0,
    "uncertain_edit_count": 0,
    "edit_width_stats": {
      "max_span": 0,
      "avg_span": 0,
      "multi_token_edits": 0
    }
  }
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

The script includes a `post_classify_other` function that reclassifies ERRANT's OTHER and R:OTHER results:
- Auxiliary verb changes (don't/didn't/was/were etc.) → `R:VERB:TENSE`
- Spelling (high Levenshtein similarity > 0.55)
- Orthography (case/whitespace only)
- Morphology (shared prefix)
- Determiner/article changes
- Preposition changes

## Double-check pass

The pipeline runs correction at **two temperatures** and intersects the edits:

| Pass | Temperature | Purpose |
|------|-------------|---------|
| Pass 1 | 0.1 | Conservative, high-precision corrections |
| Pass 2 | 0.3 | Slightly more permissive, catches subtle errors |

Only edits present in **both** passes are used in the final output. Edits found only in one pass are counted in `metadata.uncertain_edit_count`. This approximates the edit-level majority voting technique from Goto et al. (2025), filtering out model hallucinations and overcorrections.

## Overcorrection detection

Edits spanning more than 3 tokens in the original text are flagged as potential overcorrections. These are counted in `metadata.overcorrection_count` with details in `metadata.overcorrection_warnings[]`. This helps downstream consumers identify likely fluency edits rather than minimal corrections.

## Noop / identity handling

If the model returns text identical to the original (whitespace-normalized), ERRANT analysis is skipped entirely and `metadata.identity_check` is set to `true`. This prevents spurious edits from tokenization differences.

## Metadata fields

The output JSON includes a `metadata` block with processing quality indicators:
- `identity_check`: true if no corrections were needed
- `overcorrection_count`: number of edits spanning >3 tokens
- `overcorrection_warnings[]`: details of each potential overcorrection
- `total_edit_count`: raw count of ERRANT edits before filtering
- `uncertain_edit_count`: edits found in only one of the two double-check passes
- `edit_width_stats.max_span / avg_span / multi_token_edits`: edit size distribution

## Codebase research via gh

If ERRANT produces unexpected output, use `gh api` to inspect the live upstream source — no clone needed:

```bash
# View classifier source (classification rules)
gh api repos/chrisjbryant/errant/contents/errant/en/classifier.py | python -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# View merger source (edit merging logic)
gh api repos/chrisjbryant/errant/contents/errant/en/merger.py | python -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# View latest commits touching a file
gh api repos/chrisjbryant/errant/commits?path=errant/en/classifier.py | python -c "import sys,json; [print(c['commit']['message'].split(chr(10))[0]) for c in json.load(sys.stdin)]"
```

Research from actual source — never hallucinate fixes.
