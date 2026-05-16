# Skill: errant-analysis

## Purpose

Take transcribed student essay JSONs (output from `ingest-images`), generate a grammatically corrected version using a cloud AI model, run ERRANT to classify each correction by error type, and produce a structured JSON report with error counts, examples, markup, and error rate.

## Files

| Item | Path |
|------|------|
| Word count script | `src/add_word_count.py` |
| Script | `src/errant_analysis.py` |
| Supabase setup | `src/setup_error_analysis.py` |
| Tests | `tests/test_errant.py` |
| Fixtures | `tests/fixtures/error_golden.json` |

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set environment variables (see Configuration table below).

## Input

Select one of the JSON files from `outputs/`. These are produced by the `ingest-images` skill and contain `student_id` and `student_text`.

## Pre-processing

Before ERRANT analysis, run `python src/add_word_count.py` to count the actual words in each essay (splits on whitespace). This writes a `word_count` key to each input JSON, used later for error rate calculation.

## Output

Saved to `local-working/{folder}-{record_id}.json`:

```json
{
  "student_id": "12345",
  "record_id": 67890,
  "submission_date": "2024-06-15T09:00:00+00:00",
  "topic": "Social Issue Opinion",
  "original_text": "...",
  "corrected_text": "...",
  "sentence_pairs": [],
  "errant_analysis": {
    "errors": [
      {"type": "R:SPELL", "count": 5, "example": "recieve -> receive"},
      {"type": "R:DET", "count": 3, "example": "a -> an"}
    ],
    "uncategorised": []
  },
  "corrected_typst": "...",
  "error_rate": 30,
  "metadata": {
    "model": "gpt-4o-mini",
    "summary_model": "gpt-4o-mini",
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

## Supabase upload

After ERRANT analysis completes, the pipeline inserts a row into the `error_reports` Supabase table with:

- `student_id`, `class`, `name`, `error_percent`, `summary`, `word_count` — base fields
- `record_id`, `submission_date`, `topic` — per-record metadata for identifying individual writing submissions
- **45 error code columns** (`r_spell`, `r_det`, `r_verb_tense`, `m_noun`, `u_punct`, etc.) — one per ERRANT code, populated with the count for that record (0 if none)

The code-to-column mapping is defined in `ERRANT_CODE_TO_COLUMN` (line ~184 of `src/errant_analysis.py`). Colon-delimited codes like `R:NOUN:NUM` are sanitized to `r_noun_num`. All 45 codes are mapped:

| Group | Column names |
|-------|-------------|
| R: (24) | `r_noun`, `r_noun_num`, `r_noun_poss`, `r_noun_infl`, `r_verb`, `r_verb_tense`, `r_verb_sva`, `r_verb_form`, `r_verb_infl`, `r_adj`, `r_adj_form`, `r_adv`, `r_prep`, `r_pron`, `r_det`, `r_conj`, `r_part`, `r_punct`, `r_spell`, `r_orth`, `r_morph`, `r_wo`, `r_contr` |
| M: (11) | `m_noun`, `m_noun_num`, `m_verb`, `m_verb_tense`, `m_verb_form`, `m_prep`, `m_pron`, `m_det`, `m_conj`, `m_part`, `m_punct` |
| U: (8) | `u_noun`, `u_verb`, `u_prep`, `u_pron`, `u_det`, `u_conj`, `u_part`, `u_punct` |
| Other (2) | `other`, `unk` |

**Setup**: Run `python src/setup_error_analysis.py` to add the columns to `error_reports`. Requires `SUPABASE_DB_URL` in `.env` (get from Supabase Dashboard → Project Settings → Database → Connection string URI). Falls back to printing SQL if DB_URL not set.

## Configuration

| Config | Value |
|--------|-------|
| Provider | OpenAI direct API |
| Correction model | `gpt-4o-mini` |
| Summary model | `gpt-4o-mini` |
| Input price | $0.15 / 1M tokens |
| Output price | $0.60 / 1M tokens |
| Correction temperatures | 0.1, 0.3, 0.5, 0.7 (4 passes, majority voting ≥3) |
| Summary temperature | 0.8 |
| Context guard | 32K tokens |
| Rate limiting | exponential backoff (2^n + jitter) on errors |
| Jitter | 0.5–1.5s between API calls |
| API key | `OPENAI_API_KEY` in `.env` or environment |
| Supabase URL | `SUPABASE_URL` in `.env` |
| Supabase key | `SUPABASE_ESL_KEY` in `.env` |
| DB connection | `SUPABASE_DB_URL` in `.env` (for `setup_error_analysis.py` only) |
| Parallel workers | 5 (`ThreadPoolExecutor`) |

## Cost estimate

A 150-word essay (~200 tokens) costs roughly:
- Correction (4 passes): $0.00052 per student
- Summary: $0.00016 per student
- **Total: ~$0.00068 per student** (~$0.07 for 100 students)

At scale using gpt-4o-mini: $0.10 for 150 students (full pipeline: correction + summary).

## ERRANT uncategorised handling

The script includes a `post_classify_other` function that reclassifies ERRANT's OTHER and R:OTHER results:
- Auxiliary verb changes (don't/didn't/was/were etc.) → `R:VERB:TENSE`
- Spelling (high Levenshtein similarity > 0.55)
- Orthography (case/whitespace only)
- Morphology (shared prefix)
- Determiner/article changes
- Preposition changes

## Multi-pass voting (edit-level majority voting)

The pipeline runs correction at **4 temperatures** and applies edit-level majority voting:

| Pass | Temperature | Purpose |
|------|-------------|---------|
| Pass 1 | 0.1 | Conservative, high-precision corrections |
| Pass 2 | 0.3 | Slightly more permissive, catches subtle errors |
| Pass 3 | 0.5 | Moderate diversity, catches alternative patterns |
| Pass 4 | 0.7 | Maximum diversity, broad coverage |

Only edits present in **at least 3 of 4 passes** are used in the final output. This implements the edit-level majority voting technique from Goto et al. (2025), which the paper shows improves F0.5 by up to 14 points on low-error-density datasets. The threshold of 3 out of 4 provides high precision: the paper demonstrates that edit frequency positively correlates with precision (Figure 3 in their paper). Edits found in fewer than 3 passes are counted in `metadata.uncertain_edit_count`.

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
