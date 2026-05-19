# Skill: errant-analysis

## Purpose

A production-grade automated ERRANT pipeline for ESL student writing analysis. Takes transcribed student essays, generates grammatically corrected versions using gpt-4o-mini with **edit-level majority voting** (2 passes, both must agree), runs ERRANT with **consistent tokenization alignment**, and produces structured JSON reports with error classification, personalised AI summaries, and Supabase persistence.

---

## Architecture

```
research_prep.py → outputs/research/{record_id}.json   (per-record input)
                        ↓
errant_analysis.py --batch                              (batch mode)
                        ↓
local-working/{folder}-{record_id}.json                 (per-record output)
                        ↓
Supabase error_reports table                            (persistence)
```

## Research Prep (`research_prep.py`)

Before batch analysis, run `python src/research_prep.py` to:

1. Fetch `student_submissions` records from Supabase (filter: skill='Writing')
2. Strip HTML tags (`<br>` → newline)
3. Filter to records with ≥40 words (shorter essays are skipped)
4. Write one JSON per record to `outputs/research/{record_id}.json` with:
   - `student_id`, `student_text`, `word_count`
   - `record_id`, `submission_date`, `topic` — per-record metadata
   - `name`, `class` — from classlist lookup
5. Produces ~680 records from the database

## Files

| Item | Path |
|------|------|
| Research prep | `src/research_prep.py` |
| Word count | `src/add_word_count.py` |
| Main pipeline | `src/errant_analysis.py` |
| Supabase setup | `src/setup_error_analysis.py` |
| Retry decorator | `src/_retry.py` |
| Tests | `tests/test_errant.py` |
| Fixtures | `tests/fixtures/error_golden.json` |

## Prerequisites

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set environment variables (see Configuration table below).

## Input

Batch mode reads all JSON files from `outputs/research/` (produced by `research_prep.py`). Each file contains `student_id`, `student_text`, `word_count`, and per-record metadata.

Interactive mode (`python src/errant_analysis.py` without `--batch`) lists available directories in `outputs/` for single-file processing.

## Core Pipeline: Edit-Level Majority Voting

The pipeline does **not** simply trust a single LLM correction. Instead:

```
Original text
    │
    ├── Pass 1 (temperature=0.1) ──→ corrected version A
    └── Pass 2 (temperature=0.5) ──→ corrected version B
              │
              ▼
      ERTRANTS on version A → edit list A
      ERTRANTS on version B → edit list B
              │
              ▼
      intersect_edits(threshold=2) — keep only edits
      found in BOTH passes
              │
              ▼
      Final confirmed edits
      (VOTE_THRESHOLD=2, both must agree)
```

**Literature basis**: Goto et al. (2026) demonstrate that edit-level majority voting improves F0.5 by up to 14 points on low-error-density datasets. Omelianchuk et al. (2024) show optimal Nmin ≈ Nsys/2 for majority voting ensembles. This pipeline uses Nsys=2, Nmin=2, prioritising precision for pedagogical feedback.

**Quality signal**: `metadata.uncertain_edit_count` reports how many edits appeared in only one pass — a direct measure of voting divergence. A count of 0 means both passes fully agreed.

## Consistent Tokenization

ERRANT's alignment algorithm compares token-by-token between original and corrected. If the two texts use different tokenization, **edit spans become misaligned**.

The pipeline uses `annotator.parse()` for BOTH original and corrected texts (whitespace-split + POS tagging), ensuring consistent token bounds. Raw `nlp()` (spaCy full tokenizer) is used only for sentence boundary detection in the Typst report.

**Consequence of inconsistency**: Without this fix, "Freedom.First" becomes 3 tokens (spaCy) in the original vs 1 token (ERRANT whitespace split) in the corrected, throwing off all subsequent edit indices. This pipeline corrects that.

## Content-Based Sentence Alignment

Sentence pairs (used in the Typst report) are aligned by **token set similarity** rather than index-order.

| Method | Behaviour | This pipeline |
|--------|-----------|---------------|
| Index-order | `orig[i] ↔ cor[i]` | ❌ Fails when sentence counts differ |
| Jaccard overlap | Exact word match | ❌ Misses spelling variants |
| **RapidFuzz token_set_ratio** | Token set similarity | ✅ Handles spelling, insertion, deletion |

Threshold: ≥0.30. Unmatched sentences are merged into adjacent pairs.

## Post-Classification Heuristic (`post_classify_other`)

ERRANT's raw classifier leaves some edits as `OTHER` or `R:OTHER`. The pipeline reclassifies these through a priority-ordered heuristic chain:

1. **Auxiliary verb changes** → `R:VERB:TENSE` (don't→doesn't, was→were, etc.)
2. **Levenshtein similarity > 0.55** → `R:SPELL` (spelling error) with **trailing punctuation stripped** so period-attached tokens don't break similarity
3. **Same text (case only)** → `R:ORTH` (capitalisation)
4. **Same text (punctuation only)** → `R:ORTH` (spacing/punctuation)
5. **Shared prefix (≥3 chars)** → `R:MORPH` (morphological variant)
6. **Determiner/article** → `R:DET`
7. **Preposition** → `R:PREP`
8. **Fallthrough** → `OTHER` (logged in `uncategorised[]`)

The trailing-punctuation strip (added this session) prevents cases like `agen → again.` from dropping below the Levenshtein threshold (0.55 → 0.50 when period is included).

## Overcorrection Detection

Edits spanning >3 tokens (`MULTI_TOKEN_THRESHOLD=3`) are flagged as potential overcorrections — fluency edits that go beyond minimal grammar correction. These are counted in `metadata.overcorrection_count` with details in `metadata.overcorrection_warnings[]`.

## Noop / Identity Handling

If the model returns text identical to the original (whitespace-normalised), ERRANT analysis is skipped entirely and `metadata.identity_check` is set to `true`. This prevents spurious edit detection from tokenization noise.

---

## Output

Saved to `local-working/{folder}-{record_id}.json`:

```json
{
  "student_id": "12345",
  "record_id": 67890,
  "submission_date": "2024-06-15T09:00:00+00:00",
  "topic": "Social Issue Opinion",
  "original_text": "I Believe that Bully is illegal...",
  "corrected_text": "I believe that bullying is illegal...",
  "sentence_pairs": [
    {"original": "...", "corrected": "..."}
  ],
  "corrected_typst": "I #underline[believe] that #underline[bullying]...",
  "error_rate": 33,
  "word_count": 55,
  "name": "Mathew",
  "class": "M2",
  "errant_analysis": {
    "errors": [
      {"type": "R:SPELL", "count": 4, "example": "themself -> themselves"},
      {"type": "R:NOUN", "count": 4, "example": "mins -> minute"}
    ],
    "uncategorised": []
  },
  "summary": "You did a great job expressing...",
  "metadata": {
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "correction_temps": [0.1, 0.5],
    "vote_threshold": 2,
    "identity_check": false,
    "overcorrection_count": 0,
    "overcorrection_warnings": [],
    "total_edit_count": 18,
    "uncertain_edit_count": 0,
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
| `error_rate` | `total_edit_count / word_count × 100` — literature-standard |
| `corrected_typst` | Original text with `#underline[correction]` markup (Typst-native) |
| `sentence_pairs` | Content-aligned via RapidFuzz `token_set_ratio` |
| `summary` | Personalised AI feedback referencing specific error types |
| `metadata.uncertain_edit_count` | Edits found in only 1 of 2 passes — voting quality signal |
| `metadata.correction_temps` | Which temperatures were used for multi-pass voting |

---

## Supabase Upload

After ERRANT analysis completes, the pipeline inserts a row into the `error_reports` Supabase table with:

- **Base fields**: `student_id`, `class`, `name`, `error_percent`, `summary`, `word_count`
- **Record metadata**: `record_id`, `submission_date`, `topic`
- **45 error code columns** (`r_spell`, `r_det`, `r_verb_tense`, `m_noun`, `u_punct`, etc.) — one per ERRANT code, populated with the count for that record (0 if none)

The code-to-column mapping is defined in `ERRANT_CODE_TO_COLUMN` (line ~184 of `src/errant_analysis.py`). Colon-delimited codes like `R:NOUN:NUM` are sanitized to `r_noun_num`.

| Group | Column names |
|-------|-------------|
| R: (24) | `r_noun`, `r_noun_num`, `r_noun_poss`, `r_noun_infl`, `r_verb`, `r_verb_tense`, `r_verb_sva`, `r_verb_form`, `r_verb_infl`, `r_adj`, `r_adj_form`, `r_adv`, `r_prep`, `r_pron`, `r_det`, `r_conj`, `r_part`, `r_punct`, `r_spell`, `r_orth`, `r_morph`, `r_wo`, `r_contr` |
| M: (11) | `m_noun`, `m_noun_num`, `m_verb`, `m_verb_tense`, `m_verb_form`, `m_prep`, `m_pron`, `m_det`, `m_conj`, `m_part`, `m_punct` |
| U: (8) | `u_noun`, `u_verb`, `u_prep`, `u_pron`, `u_det`, `u_conj`, `u_part`, `u_punct` |
| Other (2) | `other`, `unk` |

**Setup**: Run `python src/setup_error_analysis.py` to add the columns to `error_reports`. Requires `SUPABASE_DB_URL` in `.env`. Falls back to printing SQL if DB_URL not set.

---

## OpenAI SDK Integration & Reliability

The pipeline uses the OpenAI Python SDK (v2.5.0+) directly — not raw HTTP requests — which provides proper exception types and connection pooling.

| Feature | Implementation |
|---------|---------------|
| Client lifecycle | Single reusable instance at module level |
| SDK retries | Disabled (`max_retries=0`) — custom retry handles all retry logic |
| Custom retry | Exponential backoff: `min(2^attempt + random(0,1), 60s)`, max 3 retries |
| Retryable errors | `RateLimitError` (429), `APIConnectionError`, `APITimeoutError`, `InternalServerError` (500+) |
| Non-retryable | `AuthenticationError`, `BadRequestError` — fail immediately |
| Output bound | `max_tokens=1024` prevents runaway generation |
| Timeout | `REQUEST_TIMEOUT=45s` per-request |
| Thread safety | Sync `OpenAI` client shared across 5 `ThreadPoolExecutor` workers |

---

## Progress Visualization

Batch mode shows a real-time `tqdm` progress bar:

```
Processing files:  45%|████▌    | 306/680 [00:45<00:55, 6.74file/s]
```

- **Exception-safe**: The bar is wrapped in a context manager (`with tqdm(...) as pbar:`) so it's properly closed even if an exception occurs
- **Label**: `desc="Processing files"` distinguishes the bar from other output
- **Worker messages**: All per-file output uses `tqdm.write()` (thread-safe) so messages appear above the bar without corrupting it
- **ETA**: Shows estimated remaining time, updated per-file
- **Per-file errors**: Caught inside the worker loop; error message logged via `tqdm.write()`, batch continues

---

## Configuration

| Config | Value |
|--------|-------|
| Provider | OpenAI direct API (`https://api.openai.com/v1`) |
| Correction model | `gpt-4o-mini` |
| Summary model | `gpt-4o-mini` |
| Input price | $0.15 / 1M tokens |
| Output price | $0.60 / 1M tokens |
| Correction temperatures | 0.1, 0.5 (2 passes, both must agree) |
| Summary temperature | 0.8 |
| Context guard | 32K tokens (`MODEL_CONTEXT_LIMIT`) |
| Max output tokens | 1,024 (`MAX_OUTPUT_TOKENS`) |
| Max retries | 3 |
| Retry delay | `min(2^attempt + random(0,1), 60s)` — exponential backoff with jitter and cap |
| Timeout | 45s per request |
| Parallel workers | 5 (`ThreadPoolExecutor`) |
| Error isolation | Per-file exceptions caught individually — one failure doesn't stop the batch |
| API key | `OPENAI_API_KEY` in `.env` or environment |
| Supabase URL | `SUPABASE_URL` in `.env` |
| Supabase key | `SUPABASE_ESL_KEY` in `.env` |
| DB connection | `SUPABASE_DB_URL` in `.env` (for `setup_error_analysis.py` only) |
| Progress bar | `tqdm` with context manager, desc label, ETA, thread-safe error output |

---

## Cost Estimate

A 150-word essay (~200 tokens) costs:

| Component | Tokens | Calculation | Cost |
|-----------|--------|-------------|------|
| Correction (2 passes) | 400 in + 400 out | 800 × ($0.15+$0.60)/1M | $0.00030 |
| Summary | 200 in + 100 out | 300 × ($0.15+$0.60)/1M | $0.00009 |
| **Total per student** | | | **$0.00039** |
| **Full batch (680 records)** | | | **~$0.27** |

At scale using gpt-4o-mini: $0.06 for 150 students.

---

## Multi-Pass Voting (Edit-Level Majority Voting)

### Literature basis

| Paper | Key finding |
|-------|-------------|
| Goto et al. (2026) — "Edit-level Majority Voting Mitigates Over-Correction in LLM-based GEC" | Edit frequency positively correlates with precision (Fig. 3). 4-pass voting improves F0.5 by up to 14 points on low-error-density datasets. |
| Omelianchuk et al. (2024) — "Pillars of Grammatical Error Correction" (BEA 2024) | Optimal Nmin ≈ Nsys/2 for majority voting. With Nsys=7, best F0.5 at Nmin=3. |
| Self-consistency literature (arXiv:2511.00751) | For capable models, returns diminish rapidly beyond 2-3 samples. |

### Pipeline implementation

| Pass | Temperature | Purpose |
|------|-------------|---------|
| Pass 1 | 0.1 | Conservative, high-precision, low diversity |
| Pass 2 | 0.5 | Moderate diversity, catches alternative patterns |

Only edits present in **both passes** are used in the final output. Edits found in only one pass are counted in `metadata.uncertain_edit_count`.

### Advantages over single-pass

1. **Precision guarantee**: Every confirmed edit was independently proposed by two passes — no hallucinated or one-off corrections
2. **Quality signal**: `uncertain_edit_count` directly measures model disagreement at different temperatures
3. **Research utility**: The uncertain count is a corpus-level quality signal — high uncertainty across many records might indicate systematic issues (e.g., domain mismatch, topic complexity)

---

## Metadata Fields

The output JSON includes a `metadata` block with processing quality indicators:

| Field | Description |
|-------|-------------|
| `model` | Correction model used (`gpt-4o-mini`) |
| `temperature` | Default temperature (0.1) |
| `correction_temps` | All temperatures used for multi-pass voting |
| `vote_threshold` | Edits must appear in ≥ this many passes |
| `identity_check` | `true` if no corrections were needed |
| `overcorrection_count` | Number of edits spanning >3 tokens |
| `overcorrection_warnings[]` | Details of each potential overcorrection |
| `total_edit_count` | Sum of all confirmed edits |
| `uncertain_edit_count` | Edits found in only 1 of 2 passes — voting divergence signal |
| `edit_width_stats.max_span` | Longest single edit span (tokens) |
| `edit_width_stats.avg_span` | Average edit span |
| `edit_width_stats.multi_token_edits` | Count of edits spanning >1 token |

---

## Commands

```bash
# research prep: fetch and prepare records
python src/research_prep.py

# batch processing (680 records, ~1.4 hours with 5 workers)
python src/errant_analysis.py --batch research

# interactive mode (single file)
python src/errant_analysis.py
```

---

## Codebase Research via gh — Mandatory Before Guessing ERRANT Internals

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
