# Skill: errant-analysis

## Purpose

Take transcribed student essay JSONs (output from `ingest-images`), generate a grammatically corrected version using a cloud AI model, run ERRANT to classify each correction by error type, and produce a structured JSON report with error counts, examples, markup, and error rate.

## Files

| Item | Path |
|------|------|
| Word count script | `src/add_word_count.py` |
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

## Pre-processing

Before ERRANT analysis, run `python src/add_word_count.py` to count the actual words in each essay (splits on whitespace). This writes a `word_count` key to each input JSON, used later for error rate calculation.

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
    "model": "google/gemma-4-31b-it",
    "summary_model": "google/gemma-4-31b-it",
    "temperature": 0.1,
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
| Correction model | `google/gemma-4-31b-it` |
| Summary model | `google/gemma-4-31b-it` |
| Input price | $0.12 / 1M tokens |
| Output price | $0.37 / 1M tokens |
| Correction temperature | 0.1 (pass 1), 0.3 (pass 2) |
| Summary temperature | 0.8 |
| Context guard | 32K tokens |
| Rate limiting | exponential backoff (2^n + jitter) on errors |
| Jitter | 0.5–1.5s between API calls |
| API key | `OPENROUTER_API_KEY` in `.env` or environment |
| Parallel workers | 5 (`ThreadPoolExecutor`) |

## Cost estimate

A 150-word essay (~200 tokens) costs roughly:
- Correction (2 passes): $0.00026 per student
- Summary: $0.00016 per student
- **Total: ~$0.00042 per student** (~$0.04 for 100 students)

At scale using Gemma 4 31B-it: $0.06 for 150 students (full pipeline: correction + summary).

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

## Codebase research via gh — mandatory before guessing ERRANT internals

**Do NOT guess or hallucinate** the contents of ERRANT's classifier, merger, tokenizer, or any other `errant/en/*.py` file. The agent's training data knowledge of these files is unreliable. Instead, **always fetch the real upstream source** using the commands below:

```bash
# View classifier source (classification rules)
gh api repos/chrisjbryant/errant/contents/errant/en/classifier.py | python -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# View merger source (edit merging logic)
gh api repos/chrisjbryant/errant/contents/errant/en/merger.py | python -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# View latest commits touching a file
gh api repos/chrisjbryant/errant/commits?path=errant/en/classifier.py | python -c "import sys,json; [print(c['commit']['message'].split(chr(10))[0]) for c in json.load(sys.stdin)]"
```

**Rule**: whenever you need to reason about what ERRANT does internally — a type code, a merge rule, a tokenization edge case — run the relevant `gh api` command first and read the actual source. Do not rely on training data knowledge of ERRANT's internals.
