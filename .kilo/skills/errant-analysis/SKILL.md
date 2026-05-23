# Skill: errant-analysis

## Purpose

A production-grade automated ERRANT pipeline for ESL student writing analysis. Takes transcribed student essays, generates grammatically corrected versions using **gpt-4.1-nano** with **sentence-by-sentence correction** (single pass, light-touch prompt), runs ERRANT for structured error classification, produces personalized AI summaries with **hallucination-verified example checking**, and stores results to Supabase.

---

## Architecture

```
outputs/{folder}/{student_id}.json           (transcribed input)
                        ↓
errant_analysis.py -- (interactive)          (or --batch)
                        ↓
local-working/{folder}-{student_id}.json     (per-student output)
                        ↓
Supabase error_reports table                 (persistence)
```

## Files

| Item | Path |
|------|------|
| Main pipeline | `src/errant_analysis.py` |
| Report generation | `src/generate_report.py` |
| Classlist sync | `src/supabase_classlist.py` |
| Tests | `tests/test_errant.py` |
| Fixtures | `tests/fixtures/error_golden.json` |

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set environment variables: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ESL_KEY`.

## Input

Reads JSON files from `outputs/{folder}/{student_id}.json` with keys `student_id`, `student_text`, and optionally `word_count`, `record_id`, `name`, `class`.

Interactive mode (`python src/errant_analysis.py`) lists all available files. Batch mode (`--batch`) processes all files in a directory.

## Core Pipeline

```
Original text
    │
    ▼
Sentence-by-sentence correction via gpt-4.1-nano
  (light-touch prompt, single pass)
    │
    ▼
Join corrected sentences → full corrected text
    │
    ▼
ERRANT diff: annotator.annotate(original, corrected)
  → structured error codes (R:VERB:TENSE, M:DET, R:ORTH, etc.)
    │
    ▼
Classify edits by type → ranked error list
  (with context_original + context_corrected spans)
    │
    ▼
LLM summary: few-shot examples + original + corrected text
  → warm feedback paragraph with 3 specific error points
    │
    ▼
Deterministic hallucination verification
  (every "you wrote" quote checked against original text)
    │
    ▼
Output JSON + Supabase insert
```

### Key characteristics

- **Single pass**: No multi-pass voting. gpt-4.1-nano at ~$0.00015/M tokens handles corrections reliably with conservative minimal edits.
- **Sentence-by-sentence**: Each sentence is corrected individually, producing cleaner ERRANT diffs at the token level.
- **Hallucination-verified summary**: After the LLM generates the feedback paragraph, every quotation is verified to actually exist in the student's original text. If verification fails, a fully deterministic fallback is used.
- **Few-shot style guidance**: The summary prompt includes 3 gold-standard examples ("Verb tense consistency", "Article usage", "Subject-verb agreement") that set the tone and format without constraining the LLM to specific error types.

## Consistent Tokenization

ERRANT's alignment algorithm compares token-by-token between original and corrected. The pipeline uses `annotator.parse()` for BOTH texts (whitespace-split + POS tagging), ensuring consistent token bounds. Raw `nlp()` (spaCy full tokenizer) is used only for sentence boundary detection.

## Content-Based Sentence Alignment

Sentence pairs (used in the Typst report) are aligned by **token set similarity** (RapidFuzz `token_set_ratio`) rather than index-order. Threshold: ≥0.30.

## Post-Classification Heuristic (`post_classify_other`)

ERRANT's raw classifier leaves some edits as `OTHER` or `R:OTHER`. The pipeline reclassifies these through a priority-ordered heuristic chain:

1. **Auxiliary verb changes** → `R:VERB:TENSE`
2. **Levenshtein similarity > 0.55** → `R:SPELL` (trailing punctuation stripped first)
3. **Same text (case only)** → `R:ORTH`
4. **Same text (punctuation only)** → `R:ORTH`
5. **Shared prefix (≥3 chars)** → `R:MORPH`
6. **Determiner/article** → `R:DET`
7. **Preposition** → `R:PREP`
8. **Fallthrough** → `OTHER` (logged in `uncategorised[]`)

## Overcorrection Detection

Edits spanning >3 tokens (`MULTI_TOKEN_THRESHOLD=3`) are flagged as potential overcorrections. Counted in `metadata.overcorrection_count`.

## Noop / Identity Handling

If the text is unchanged after correction, ERRANT analysis is skipped and `metadata.identity_check` is set to `true`.

---

## Output

Saved to `local-working/{folder}-{record_id}.json`:

```json
{
  "student_id": "29765",
  "record_id": 67890,
  "original_text": "I like to keep happy...",
  "corrected_text": "I like to be happy...",
  "corrected_typst": "I like to #underline[be] happy...",
  "llm_edits": [
    {"original": "I like to keep happy.", "corrected": "I like to be happy.", "edits": ["keep -> be"]}
  ],
  "sentence_pairs": [
    {"original": "...", "corrected": "..."}
  ],
  "error_rate": 37,
  "word_count": 82,
  "name": "August",
  "class": "M2-5A",
  "errant_analysis": {
    "errors": [
      {"type": "R:ORTH", "count": 4, "example": "happen -> happen,",
       "context_original": "...must happen like this...",
       "context_corrected": "...has to happen, like this..."},
      {"type": "R:NOUN", "count": 4, "example": "time -> time,"},
      {"type": "R:VERB", "count": 3, "example": "felt -> feel"}
    ],
    "uncategorised": []
  },
  "summary": "August, I really enjoyed reading...",
  "metadata": {
    "model": "gpt-4.1-nano",
    "identity_check": false,
    "overcorrection_count": 0,
    "overcorrection_warnings": [],
    "total_edit_count": 30,
    "edit_width_stats": {
      "max_span": 1,
      "avg_span": 1.0,
      "multi_token_edits": 0
    }
  }
}
```

### Key fields

| Field | Description |
|-------|-------------|
| `corrected_text` | Plain corrected text (no markup) |
| `corrected_typst` | Original text with `#underline[correction]` markup (Typst-native) |
| `llm_edits` | Per-sentence edit explanations from gpt-4.1-nano |
| `error_rate` | `total_edit_count / word_count × 100` |
| `errant_analysis.errors[].context_original` | Original text span (\(\pm\)3 tokens) around the error |
| `errant_analysis.errors[].context_corrected` | Corrected text span (\(\pm\)3 tokens) around the fix |
| `summary` | Personalised AI feedback with hallucination-verified examples |

---

## Student Info Lookup

Student name and class are looked up from the Supabase `classlists` table. If not found, the analysis continues with empty `name` and `class` fields. Missing IDs are logged at the end of a batch run.

## Supabase Upload

After ERRANT analysis completes, the pipeline inserts a row into the `error_reports` table with error code columns populated by count (0 if none). The code-to-column mapping is defined in `ERRANT_CODE_TO_COLUMN` (line ~184).

---

## OpenAI SDK Integration & Reliability

| Feature | Implementation |
|---------|---------------|
| Client lifecycle | Single reusable instance at module level |
| SDK retries | Disabled (`max_retries=0`) — custom retry handles all retry logic |
| Custom retry | Exponential backoff: `min(2^attempt + random(0,1), 60s)`, max 3 retries |
| Retryable errors | `RateLimitError` (429), `APIConnectionError`, `APITimeoutError`, `InternalServerError` (500+) |
| Non-retryable | `AuthenticationError`, `BadRequestError` — fail immediately |
| Timeout | `REQUEST_TIMEOUT=45s` per-request |
| Thread safety | Sync `OpenAI` client shared across `ThreadPoolExecutor` workers |

---

## Configuration

| Config | Value |
|--------|-------|
| Provider | OpenAI direct API (`https://api.openai.com/v1`) |
| Correction model | `gpt-4.1-nano` |
| Summary model | `gpt-4o-mini` |
| Correction input price | ~$0.00015 / 1M tokens |
| Correction output price | ~$0.00060 / 1M tokens |
| Summary input price | ~$0.15 / 1M tokens |
| Summary output price | ~$0.60 / 1M tokens |
| Correction temperature | 0.1 (single pass) |
| Summary temperature | 0.8 |
| Max retries | 3 |
| Retry delay | `min(2^attempt + random(0,1), 60s)` |
| Timeout | 45s per request |
| Parallel workers | 5 (`ThreadPoolExecutor`) |
| API key | `OPENAI_API_KEY` in `.env` or environment |
| Supabase URL | `SUPABASE_URL` in `.env` |
| Supabase key | `SUPABASE_ESL_KEY` in `.env` |

---

## Cost Estimate

A 150-word essay (~200 tokens) costs:

| Component | Tokens | Cost |
|-----------|--------|------|
| Correction (gpt-4.1-nano, 1 pass) | 200 in + 200 out | ~$0.00015 |
| Summary (gpt-4o-mini, 1 call) | 200 in + 200 out | ~$0.00019 |
| **Total per student** | | **~$0.00034** |
| **Full batch (19 students)** | | **~$0.0065** |

---

## Metadata Fields

The output JSON includes a `metadata` block:

| Field | Description |
|-------|-------------|
| `model` | Correction model used (`gpt-4.1-nano`) |
| `identity_check` | `true` if no corrections were needed |
| `overcorrection_count` | Number of edits spanning >3 tokens |
| `overcorrection_warnings[]` | Details of each potential overcorrection |
| `total_edit_count` | Sum of all confirmed edits |
| `edit_width_stats.max_span` | Longest single edit span (tokens) |
| `edit_width_stats.avg_span` | Average edit span |
| `edit_width_stats.multi_token_edits` | Count of edits spanning >1 token |

---

## Commands

```bash
# interactive mode (select file from menu)
python src/errant_analysis.py

# generate PDF report booklet
python src/generate_report.py "folder-name"
```

---

## Codebase Research via gh — Mandatory Before Guessing ERRANT Internals

**Do NOT guess or hallucinate** the contents of ERRANT's classifier, merger, tokenizer, or any other `errant/en/*.py` file. Use the relevant `gh api` command first and read the actual source.

```bash
# View classifier source
gh api repos/chrisjbryant/errant/contents/errant/en/classifier.py | python -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# View merger source
gh api repos/chrisjbryant/errant/contents/errant/en/merger.py | python -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"
```
