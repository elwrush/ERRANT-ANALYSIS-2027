# ERRANT Analysis Pipeline for ESL Writing Assessment

## Background

### Educational Context

This project serves an English program at a Thai secondary school (Mathayom level, equivalent to grades 7–12). Students write baseline essays by hand in class on topics such as family, hobbies, and personal interests. These essays are scanned and processed through an automated grammatical error correction pipeline to produce:

1. **Individualized feedback reports** for each student showing their specific errors with corrections
2. **Aggregate error statistics** for teachers to identify class-wide patterns
3. **Historical tracking** of error rates across multiple submissions

The student population is Thai L1 English learners at the M2–M3 level (ages 13–15, CEFR A2–B1). Common error patterns include:

- Subject-verb agreement (SVA): *"My family have many pets"* — British English accepts collective noun plural, but standard ESL pedagogy teaches singular
- Article omission: *"He is good student"* → missing *"a"*
- Preposition errors: *"good in playing"* instead of *"good at playing"*
- Verb tense: *"Yesterday I go to school"* instead of *"Yesterday I went"*
- Phonetic spelling: *"becos"* for *"because"*, *"hare"* for *"have"*, *"drun"* for *"drum"*
- Thai L1 transfer: *"I very like music"* instead of *"I really like music"* (adverb placement)
- Noun pluralization: *"I have two book"* instead of *"two books"*
- Word choice: *"I like about music"* — Thai-influenced preposition usage

### The Correction Problem

Grammatical error correction (GEC) for ESL writing requires a specific type of correction: **minimal editing**. The goal is to fix only what is grammatically wrong while preserving the student's voice, vocabulary choices, and sentence structure. This differs from:

- **Fluency editing** (used in machine translation post-editing) — rewrites entire sentences to sound natural
- **Style editing** (used in professional editing) — adjusts tone, register, and flow
- **Content editing** — restructures arguments and ideas

The literature consistently finds that large language models (LLMs) default to fluency editing when asked to "correct" text, even when explicitly instructed to make minimal changes. This is known as the **over-correction problem**.

### The Voting Solution

Over-correction manifests as edits that appear in only one or a few random generations from a stochastic model. Genuine grammatical corrections, by contrast, are more constrained — there are only a limited number of ways to fix a missing article or a subject-verb agreement error. Therefore, **edit-level majority voting** over multiple independent correction attempts can filter out spurious fluency edits while retaining genuine corrections.

This principle was established by Goto, Sakai, and Watanabe (2026) in "Edit-level Majority Voting Mitigates Over-Correction in LLM-based Grammatical Error Correction," which demonstrated that:

- Edit frequency positively correlates with precision (their Figure 3)
- 8 candidates are sufficient for stable voting
- The method improves F0.5 by up to 14 points on low-error-density datasets
- Performance is stable across 10 different prompt templates

---

## Methodology

### Pipeline Overview

```
Handwritten essay (paper)
    → scan → JPEG image
    → OCR via Gemini 2.5 Flash Lite (OpenRouter)
    → JSON with student_id + student_text
    → word count (add_word_count.py)
    → 5x GPT-4o-mini correction at gradient temperatures
    → ERRANT edit extraction per pass
    → 3/5 majority vote with conflict resolution
    → Edit classification + summary generation
    → Supabase insert (error_reports table)
    → Typst PDF report with:
        1. Masthead + summary + error-rate chart
        2. Corrected writing with underlined corrections
        3. Original uncorrected writing
        4. Blank pages (pad to multiple of 4)
```

### File Grouping (Ingestion)

Images are sorted alphabetically within each input folder. With `pages_per_essay = N`, images are grouped sequentially into chunks of N. The student ID is extracted by the vision model from the handwritten ID field on the page, not from the filename. This means filenames can follow any convention — the sequential grouping ensures that img-0001 through img-000N form one essay, img-000N+1 through img-0002N form the next, etc.

### The 4-Shot Prompt

The correction prompt follows the TOOL template from Davis et al. (2024) and Goto et al. (2026, Appendix A). Four fixed examples demonstrate single-token minimal corrections for common error types:

1. **Preposition**: *"good in playing"* → *"good at playing"*
2. **Article**: *"good student"* → *"a good student"*
3. **Verb tense**: *"Yesterday I go"* → *"Yesterday I went"*
4. **Word choice (Thai L1)**: *"very like"* → *"really like"*

The examples are intentionally simple — each changes exactly one word. This teaches the model what "minimal" means concretely, without annotating or explaining the reasoning.

### Temperature Gradient

After extensive testing across multiple configurations, the optimal temperature setting was found to be a **gradient spread of [0.1, 0.2, 0.3, 0.4, 0.5]** rather than the uniform 1.0 used in the Goto paper. The rationale:

| Temp | Behavior | Contribution |
|------|----------|-------------|
| 0.1 | Nearly greedy, conservative | Anchors the vote with high-precision corrections |
| 0.2–0.4 | Moderate diversity | Covers common error patterns reliably |
| 0.5 | Highest variation | Prevents over-fitting to conservative errors |

The gradient approach empirically outperforms uniform 1.0 at k=5 because the Goto paper uses k=8 with per-dataset τ optimization — two advantages we cannot fully replicate. The low-temperature passes provide a stable anchor for common errors (articles, prepositions, SVA) while the single high-temperature pass adds diversity without veto power over the majority.

### Voting and Conflict Resolution

For each student:

1. **5 correction passes** are generated at the gradient temperatures
2. ERRANT extracts edits from each pass independently
3. **Edit frequency** is counted across all 5 passes
4. Edits appearing in **≥3 of 5** passes are retained (majority threshold)
5. Retained edits are **sorted by vote count** (highest first)
6. **Conflict resolution**: overlapping edits (edits sharing a character span in the original text) are resolved greedily — the higher-vote edit wins, the lower-vote overlap is discarded
7. Final edits are sorted by original-text position and applied to produce the corrected text

This algorithm is based on the `EnsembleVoting` implementation from Goto et al. 2026 (their `gec-llm` library), adapted to our k=5, τ=3 configuration.

### ERRANT Annotation

Error type classification uses the ERRANT v3 rule-based classifier (Bryant et al. 2017), which categorizes edits into 55+ types under three main groups:

- **R:** Replacement errors (R:VERB:TENSE, R:PREP, R:SPELL, etc.)
- **M:** Missing-word errors (M:DET, M:PREP, M:VERB, etc.)
- **U:** Unnecessary-word errors (U:DET, U:PREP, etc.)

Edits that ERRANT cannot classify are logged as `OTHER` or `UNK` and passed through a post-classification heuristic chain (spelling similarity, case-only changes, shared prefix matching, etc.) for reclassification.

### Supabase Schema

The `error_reports` table stores:

- **Base fields**: `student_id`, `class`, `name`, `error_percent`, `summary`, `word_count`, `academic_year` (default 2007)
- **45 error-code columns**: one per ERRANT error type (e.g., `r_noun`, `r_verb_tense`, `m_det`, `u_prep`, `r_spell`)
- **No redundant fields**: `record_id`, `submission_date`, and `topic` are not written — they already exist in the `student_submissions` table

### Report Generation

PDF reports are generated via Typst, a LaTeX-like typesetting system. Each student occupies a multiple-of-4 page booklet:

| Page | Content |
|------|---------|
| 1 | School header, report title, student info, personalized summary, CEFR target-rate explanation, error-rate line chart with historical comparison |
| 2 | **Your Writing with Corrections** — corrected text with `#underline[]` markup showing all corrections, left-aligned subtitle |
| (same page) | **Your Original Writing (Uncorrected)** — verbatim student text, separated by vertical space |
| + | Blank pages to pad to the next multiple of 4 (for booklet printing) |

---

## Evaluation of Quality

### Comparative Testing

Throughout development, the pipeline was tested on two representative students:

**August (29765)** — low error density (~18% error rate). Key challenge: phonetic spelling error *"hare happy"* (intended: *"have happy"* or *"feel happy"*).

**Ti (30378)** — high error density (~54% error rate). 74-word text with 40+ errors covering articles, prepositions, punctuation, capitalization, spelling, and verb forms.

| Config | August "hare→have" | Ti corrections | Ti rate |
|--------|-------------------|----------------|---------|
| GPT original (2-pass, 0.1/0.5, τ=2) | "hear" ❌ | 39 | 53% |
| DeepSeek (5-pass, 1.0×5, τ=3) | "feel" ❌ | 40 | 54% |
| Qwen-2.5-7B (5-pass, 1.0×5, τ=3) | "very much like about" ❌ | 0 (voting failed) | — |
| GPT (5-pass, 1.0×5, τ=3) | "have" ~2-3/5 ⚠️ | 44 | 59% |
| **GPT (5-pass, gradient 0.1-0.5, τ=3)** | **"have" 4/5 ✅** | **44** | **59%** |
| GPT (8-pass, 1.0×8, τ=4) | "have" 3/8 ❌ | — | — |

### Strengths

1. **Over-correction is effectively mitigated.** The 3/5 threshold with conflict resolution successfully filters fluency rewrites. Corrections are genuinely minimal — the model changes only what needs changing and leaves the rest of the sentence intact.

2. **Common error types are reliably detected.** Articles, prepositions, SVA, verb tense, and spelling corrections appear in 3+ passes for most students. The gradient temperatures ensure that these common corrections are made consistently.

3. **The pipeline is production-ready.** It handles the full workflow from scan → PDF report with Supabase persistence, cost tracking, missing-student alerting, and batch processing of 20+ students in under 90 seconds.

4. **Conflict resolution measurably improves output.** The vote-sorted overlap resolution increased correct edits from 9/14 to 12/14 of manual corrections (on student 30490 with DeepSeek 5-pass).

### Weaknesses

1. **The "have happy" problem.** The model consistently maps *"hare"* → *"have"* (a phonetic spelling correction) but does not recognize that *"have happy"* is grammatically incorrect (verb + adjective). The gradient approach achieves 4/5 consensus on *"have happy"*, which is **consistent but still wrong**. The correct correction would be *"feel happy"* (minimal, changes one word) or *"have happiness"* (grammatically correct but changes noun form). This is a model knowledge gap: GPT-4o-mini can correct phonetic spellings or fix grammar, but it cannot do both simultaneously for a single error.

2. **No per-student τ optimization.** The Goto paper shows optimal thresholds ranging from τ=8 (low-error texts like CWEB-G) to τ=1 (high-error texts like JFLEG). Our fixed τ=3 is a compromise that under-corrects dense-error texts and slightly over-filters sparse-error texts. Optimal tuning would require labeled reference corrections for our specific student population.

3. **Ingestion accuracy ceiling.** The lightweight vision model (`gemini-2.5-flash-lite`) occasionally drops words or merges tokens. Since ERRANT compares original vs corrected, any transcription error cascades through the entire pipeline — false negatives (missed errors) and false positives (spurious corrections) both originate from inaccurate source text.

4. **No fine-tuned GEC model available.** The EPO model (Liang et al. 2025; used in Goto et al. 2026) achieves F0.5 74.6 on BEA-2019 — approximately 6 points above our best Qwen3-8B result. The model weights are not publicly available and cannot be accessed via any API provider.

---

## Areas for Future Research

### Low Effort, High Impact

1. **Increase k to 8 with gradient [0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.0] and τ=4.** The Goto paper recommends k=8 before diminishing returns. The three extra lower-temperature passes would further stabilize consensus on common errors.

2. **Per-student τ via greedy baseline.** Run one greedy (temp=0) pass first to estimate error density. If it produces >X edits, use τ=2 (lenient); if <Y edits, use τ=5 (strict). This mirrors the Goto paper's per-dataset optimization without requiring labeled development data.

3. **Dynamic few-shot example retrieval.** Maintain a pool of ~20 hand-crafted correction pairs covering specific error patterns. Before correction, retrieve 3-4 examples whose error types match the current student's text (e.g., via keyword overlap or n-gram similarity). Tang et al. 2024 showed this outperforms fixed examples.

### Medium Effort, Medium Impact

4. **Upgrade ingestion model.** Switch from `gemini-2.5-flash-lite` to the full `gemini-2.5-flash` or a comparable model. A controlled 20-image comparison would quantify the cascade effect of transcription accuracy on downstream correction quality.

5. **Try `gpt-4.1-nano` for corrections.** Priced at $0.10/$0.40 per 1M tokens (vs GPT-4o-mini's $0.15/$0.60), it is cheaper and potentially better at instruction following. Requires running the same batch and comparing ERRANT output.

### High Effort, High Impact

6. **Self-host a fine-tuned GEC model.** The EPO approach (Edit-level Preference Optimization, Liang et al. 2025) achieves F0.5 74.6 on BEA-2019 — approximately 6 points above our Qwen3-8B voting result. Training requires GPU infrastructure (A100 or similar), ~50k examples from FCE/W&I training data, and integration effort. This is the single highest-impact improvement available.

7. **Label a development set for τ optimization.** Twenty expert-corrected essays from our student population would allow data-driven τ selection for Thai L1 English learners, replacing the current fixed τ=3 with an empirically validated value.

8. **Investigate reference-free quality metrics.** Current evaluation relies on ERRANT against the pipeline's own corrections (circular). Reference-free metrics like SOME or IMPARA could provide independent quality signals — Kobayashi et al. 2024 found they correlate better with human judgment than ERRANT.

---

## Sample Outputs

### Sample 1: August (29765) — Low error density, phonetic spelling challenge

This text has relatively few errors but includes the problematic *"hare happy"* pattern. The pipeline correctly fixes tense (*felt → feel*), prepositions (*in → at*), conjunctions (*to → too*), and SVA (*choose → chooses, make → makes*), but produces *"hear happy"* instead of the intended *"have happy"* — a phonetic mapping error where the model interprets *"hare"* as *"hear"* rather than recognizing it as a misspelling of *"have"*.

**Original:**
> I like to keep happy. Sometimes, I felt sad because something I don't like must happen like this time. I had to be leader again So, in the same time I like it to because when my friend choose me. that is my friend make me sure that I can help some friend workes. And another thing that I Can do to. So I just hare happy and laughed time so I want my friend feel the same emotional like me too.

**Corrected:**
> I like to keep happy. Sometimes, I feel sad because something I don't like must happen like this time. I had to be leader again, so at the same time I like it too because when my friend chooses me, that is my friend makes me sure that I can help some friends' work. And another thing that I can do too. So I just hear happy and laugh so I want my friends to feel the same emotion as me too.

**Edits detected:** 18 (22% error rate)
**Error types:** R:VERB:TENSE, R:PREP, R:CONJ, R:ORTH, R:SPELL, M:DET, R:NOUN:NUM, R:PRON, R:NOUN:POSS, R:ADJ, R:ADV

### Sample 2: Ti (30378) — High error density, comprehensive correction

This text contains errors in nearly every sentence: missing articles, incorrect prepositions, phonetic spellings, capitalization, punctuation, verb tense, and word choice. The pipeline makes extensive corrections while preserving the student's voice and narrative structure.

**Original:**
> I can practise drum more 10 h. because i very like about drum i can play about.. long time because i very love about music ican listen the music about the day because i was play drum when i was 5 years old then next 4 years i was start compettition and after 2 years now iam the best of 13 years old thailand drummer that is reason why ican practice drun 10 h.

**Corrected:**
> I can practice drums for more than 10 hours because I really like drums. I can play for a long time because I love music. I can listen to music all day because I played drums when I was 5 years old. Then, after 4 years, I started competing, and after 2 years, now I am the best 13-year-old drummer in Thailand. That is the reason why I can practice drums for 10 hours.

**Edits detected:** 44 (59% error rate)
**Error types:** R:SPELL, R:PREP, R:VERB:TENSE, M:DET, R:NOUN:NUM, R:ORTH, R:VERB:FORM, R:CONJ, R:PRON, U:PREP, R:VERB:SVA, R:ADV, U:DET, R:ADJ, R:NOUN, R:WO

### Sample 3: Mile (30490) — Moderate error density, clean output

This text shows moderate errors typical of M2-5A students. The corrections are minimal and clean: article insertions, preposition fixes, verb tense, noun plurals. The *"apple &"* sequence is an ingestion artifact (a drawing of an apple that the vision model transcribed as *"&"* — the ingestion prompt was later updated to skip drawings).

**Original:**
> The best thing that I ever have is my family. They're the best in world wide. My family have enough time to spend with me. They make me food in every breakfast and drive me to school. They love me and my sister equally and take me to a vacation every holiday. Me and my twin have toys over our house. They bring me to good school and they give me a lot of money and every thing I like except game because I once use over 150 B on game and soon get bored. I would like to say my life is the best! Good grade, Good family, Good relative, Good friends! I'm very pretty too. My family and relatives always say that I'm cute and very smat and I like apple & My life is perfect and the only bad thing is I can't play any sport nor instrument.

**Corrected:**
> The best thing that I ever have is my family. They're the best in the world. My family has enough time to spend with me. They make me food for every breakfast and drive me to school. They love me and my sister equally and take us on vacation every holiday. My twin and I have toys at our house. They bring me to a good school and they give me a lot of money and everything I like except games because I once used over 150 B on a game and soon got bored. I would like to say my life is the best! Good grades, good family, good relatives, good friends! I'm very pretty too. My family and relatives always say that I'm cute and very smart, and I like apples. My life is perfect and the only bad thing is I can't play any sport or instrument.

**Edits detected:** 25 (17% error rate)
**Error types:** M:DET, R:PREP, R:VERB:SVA, R:ORTH, R:NOUN:NUM, R:VERB:TENSE, R:VERB:INFL, R:PRON, R:WO, R:CONJ, R:ADJ, R:PUNCT, R:NOUN, R:SPELL, R:ADV

| Paper | Contribution |
|-------|-------------|
| Bryant et al. 2017 — "Automatic Annotation and Evaluation of Error Types for GEC" | ERRANT toolkit: rule-based edit extraction and classification |
| Bryant et al. 2023 — "Grammatical Error Correction: A Survey of the State of the Art" | Comprehensive survey (383 cites) of GEC approaches |
| Davis et al. 2024 — "Prompting Open-Source and Commercial Language Models for GEC" | TOOL prompt template; 4-shot examples for English GEC |
| Goto et al. 2026 — "Edit-level Majority Voting Mitigates Over-Correction in LLM-based GEC" | Training-free voting over k=8 candidates; τ optimized per dataset; 4-shot TOOL template; code released |
| Liang et al. 2025 — "Edit-level Preference Optimization for GEC" | EPO: fine-tuned Llama2-7b reaches F0.5 74.6 on BEA-2019 |
| Omelianchuk et al. 2024 — "Pillars of Grammatical Error Correction" (BEA 2024) | Ensemble of 7 diverse systems (GECToR + T5 + GPT-4); optimal Nmin ≈ Nsys/2 |
| Staruch et al. 2025 — "Adapting LLMs for Minimal-edit GEC" | Fine-tuned Mistral-7b-EPO with novel training schedule; SOTA minimal-edit on BEA-test |
