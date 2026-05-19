# Research Plan: ERRANT Analysis Interpretation Framework

## Dataset Summary

| Dimension | Value |
|-----------|-------|
| Total files | 689 research-XXXXX.json |
| **Class-label convention** | **M2 = currently enrolled (in classlist); M3 = left the program (not in classlist).** Not academic level — the label reflects enrollment status. |
| Active (M2 label) | 36 students, 289 files. All verified as currently enrolled via Supabase classlist cross-reference. From academic levels M3-4A (18) and M3-5A (18) in the paper classlist, but marked M2 because they're enrolled. |
| Former (M3 label) | 36 students, 400 files. IDs not found in classlist — assumed to have left the program. |
| Longitudinal scope | **70 of 72 students have 2–15 submissions each** (not just 3). Only 2 students have single submissions. Mean submissions per student: ~9.6. |
| Key fields per file | `student_id`, `class` (M2=active/M3=former), `name`, `word_count`, `error_rate`, `errant_analysis.errors` (array of `{type, count, example}`), `errant_analysis.uncategorised`, `metadata` (overcorrection_count, total_edit_count, edit_width_stats, uncertain_edit_count), `summary`, `topic`, `submission_date`, `record_id` |
| ERRANT error types | 55 possible codes across Replacement, Missing, and Unnecessary operations (R:*, M:*, U:*, OTHER, UNK) |
| Identity-check files | **Zero.** Every file has at least one detected error. No ceiling effect. |

---

## Research Questions

### RQ1 [Topline — Error prevalence by cohort]

**What are the most frequent grammatical error types in M2 and M3 learner writing, and how do their relative frequency rankings differ between the two cohorts?**

*Approach:* Aggregate `errant_analysis.errors[*].count` by error type, normalised per 100 words, separately for M2 and M3. Produce ranked tables and side-by-side comparison of the top-15 error types per cohort. Prior research on proficiency-level error profiling (Beginners: tense/verb-form dominant; Advanced: determiners, prepositions, complex structures) provides an expected gradient against which to compare findings. Secondary cut: within-cohort breakdown by sub-class (M2-4A vs M2-5A; M3-3A, M3-4A, M3-5A via `docs/students.txt` cross-reference) to identify potential classroom-level effects.

*Variables:* Cohort (M2/M3, categorical IV); error type frequency (continuous DV, normalised per 100 words).

*From preliminary 50-file sample:* R:ORTH (353), R:NOUN (333), R:SPELL (327), R:NOUN:NUM (224), R:VERB:SVA (156).

---

### RQ2 [Topline — Error-rate thresholding]

**To what extent do M2 and M3 cohorts differ in the proportion of students whose mean error rate exceeds a threshold of (a) 10%, (b) 15%, (c) 20%, and (d) 25%?**

*Approach:* Compute per-student aggregate error rate (mean across all their submissions). Evaluate cumulative distribution at each threshold, split by cohort. Benchmark candidate thresholds against the Write & Improve Corpus 2024 (Nicholls et al.), which provides CEFR-labelled error-rate norms. Produce histograms of error rates by cohort with threshold lines overlaid.

*Variables:* Cohort (M2/M3); error-rate threshold (ordinal, 4 levels); binary classification at each threshold.

---

### RQ3 [Topline — Between-cohort error composition]

**To what extent does the distribution of grammatical error types differ between active (M2) and former (M3) students when controlling for text length, and which specific error categories exhibit the largest divergence between the two groups?**

*Approach:* Normalise per-student error counts by word count (errors per 100 words). Apply Mann-Whitney U or permutation tests per error type with Bonferroni correction for multiple comparisons. Report effect sizes (Cliff's δ) and rank error types by magnitude of difference. Generate a differential heatmap. The comparison is between students who stayed in the program (M2 label) and those who left (M3 label). A systematic difference in error profiles — particularly if former students show higher rates of specific error types — may signal difficulties that contributed to attrition.

*Variables:* Enrollment status (active=M2, former=M3, IV); normalised error count per type (DV per test); word count (covariate).

*Preliminary finding:* Mean error rate 15.7% (active) vs 16.2% (former). Small overall difference, but distribution shapes differ notably at the upper end.

---

### RQ4 [Longitudinal — Error trajectory]

**How do overall error rate and constituent error-type frequencies change across repeated writing submissions for individual learners, and to what extent do these trajectories differ between students who remained enrolled and those who left the program?**

*Scope:* 70 of 72 students have 2–15 submissions (mean ~9.6). This is a genuine longitudinal dataset, not a pilot.

*Approach:*
1. Per-student slope: Fit a linear or loess trend to each student's error_rate over submission_date (or submission_number if dates are sparse). Extract the slope coefficient (rate of change per submission).
2. Classify each student as improving (negative slope, p<0.10), stable, or regressing (positive slope, p<0.10).
3. Compare proportions of improving/stable/regressing students between active (M2) and former (M3) groups using χ² test.
4. Per-error-type trajectories: For the top-10 most frequent error types, compute per-student slopes. Aggregate across students to produce cohort-level trajectory profiles. Classify each error type as "commonly resolving" (≥50% of students show negative slope), "commonly persistent" (<25% of students show negative slope), or "mixed."
5. Mixed-effects modelling (optional, if data supports): Fit `error_rate ~ submission_number * group + (1 | student_id)` to test whether the rate of improvement differs between active and former students while controlling for individual variation. Reference: Thewissen (2013) — "Capturing L2 accuracy developmental patterns" — found distinct developmental trajectories across error-type categories in a longitudinal EFL corpus.

*Variables:* Submission number (ordinal, within-student IV); enrollment status (active/former, between-student IV); error rate and per-type counts (DVs).

---

### RQ5 [Longitudinal — Overcorrection stability]

**To what extent does the automated overcorrection rate vary over a student's submission history, and is higher overcorrection associated with higher overall error rates, larger edit spans, or eventual program attrition?**

*Approach:*
1. **Within-student overcorrection trajectory:** For each multi-submission student, compute `overcorrection_ratio = overcorrection_count / total_edit_count` per submission. Plot trajectory over submission_number. Test whether the ratio increases (model becomes less reliable as writing gets more complex) or remains stable.
2. **Cross-sectional group difference:** Compare mean overcorrection_ratio between active (M2) and former (M3) students using Mann-Whitney U. If former students have higher ratios, it may indicate that the model was less reliable for struggling writers whose scores are therefore less trustworthy.
3. **Correlational:** Spearman's ρ between `overcorrection_ratio` and `error_rate` across all files. If positive, the correction model is least reliable for the students who need it most.
4. **Multi-variable analysis:** Examine correlation between overcorrection_ratio and `multi_token_edits` (from edit_width_stats) — multi-token edits are a proxy for model overreach.

*Variables:* Overcorrection ratio (DV); submission order (within-student IV); enrollment status (between-student IV); error rate, edit span (predictors).

---

### RQ6 [Cohort — Topic sensitivity]

**To what extent does the writing task topic influence the frequency and distribution of grammatical error types in M2 and M3 EFL learner writing?**

*Approach:* Group submissions by the `topic` field. Compute per-topic error-type profiles. Test the hypothesis — derived from genre-based SLA research — that narrative prompts (e.g., "what makes you laugh?") elicit disproportionately high R:VERB:TENSE and R:PUNCT errors, while argumentative or transactional prompts (e.g., "should mobile phones be allowed?") increase R:WO, R:CONJ, and M:DET errors. This distinction matters for data interpretation: an apparent between-cohort difference in verb errors may reflect unequal topic distribution rather than genuine developmental differences.

*Variables:* Topic (categorical IV); normalised error-type counts (DVs); cohort (moderator).

---

### RQ7 [Cohort — Sub-class effects]

**To what extent do mean error rates and error-type profiles differ between the two academic sub-classes within the active-student cohort (M3-4A vs M3-5A, both labelled M2 in the data), and can such differences be attributed to instructional effects rather than intake variation?**

*Approach:* Cross-reference `student_id` with `docs/students.txt` to assign sub-class (M3-4A or M3-5A) to the 36 active students. Compare mean error rates and error-type distributions across sub-classes using Mann-Whitney U tests (since this is a two-group comparison). Report effect sizes (Cliff's δ). If significant differences emerge, test the confound of topic distribution (χ²) — one sub-class may have written on systematically different prompts.

*Caveat:* The 36 former (M3-labelled) students are not in students.txt, so sub-class is unknown. They are excluded from this analysis.

*Variables:* Sub-class (M3-4A / M3-5A, categorical IV); mean error rate, per-type normalised error counts (DVs).

---

### RQ8 [Cohort — Text length and error rate]

**What is the nature and magnitude of the relationship between text length (word count) and grammatical error rate in M2 and M3 learner writing, and to what extent does this relationship differ between cohorts?**

*Approach:* Compute Pearson/Spearman correlation between `word_count` and `error_rate` for each cohort separately and combined. Longer texts provide more opportunities for error, but may also reflect greater writing fluency and confidence. A negative correlation would suggest that more proficient students write more and make fewer errors. Produce scatter plots with regression lines per cohort.

*Variables:* Word count (continuous IV); error rate (continuous DV); cohort (moderator).

---

### RQ9 [Methodology — Uncategorised errors]

**What proportion of edits identified by the ERRANT annotation pipeline remain uncategorised, and what linguistic features characterise the errors that the `post_classify_other()` fallback fails to resolve?**

*Approach:* Aggregate `errant_analysis.uncategorised` across all files. Compute the proportion of total edits that are uncategorised (should be low if the pipeline is well-calibrated). Sample uncategorised orig→cor edit pairs and qualitatively examine what linguistic phenomena resist classification (e.g., idiomatic expressions, discourse-level reformulations, L1-transfer patterns). This question serves dual purposes: quality assurance for the pipeline and identification of error types the current ERRANT taxonomy cannot capture.

*Variables:* Uncategorised edit count (continuous DV); student cohort, topic (exploratory IVs).

---

### RQ10 [Individual — Error-profile clustering]

**To what extent can M2 and M3 EFL learners be grouped into distinct clusters on the basis of their normalised error-type profiles, and what are the defining error-type characteristics of each cluster?**

*Approach:* Construct a per-student feature vector of normalised error counts (errors per 100 words) across the ERRANT taxonomy. Apply dimensionality reduction (PCA or t-SNE) followed by k-means or hierarchical clustering. Evaluate cluster solutions (2–6 clusters) using silhouette scores. Interpret clusters qualitatively (e.g., "determiner-dominant," "verb-form-dominant," "spelling-punctuation-dominant," "uniformly low-error," "uniformly high-error"). Map clusters to recommended instructional groupings.

*Variables:* Error-type frequency vector per student (multivariate input); cluster assignment (categorical output).

---

### RQ11 [Individual — Outlier detection]

**Which individual learners in each cohort demonstrate outlier error patterns — in terms of exceptionally high error rate, single-type error dominance, or high overcorrection rate — and what do these profiles suggest about the appropriate use of automated error analysis for such students?**

*Approach:* For each student, compute three metrics: (a) mean error rate, (b) proportion of total errors contributed by the single most frequent error type (dominance ratio), and (c) overcorrection count / total edits ratio. Flag students exceeding 2σ above cohort mean on any metric. Cross-reference flagged students against `summary` feedback for qualitative diagnostic cues. Students with high dominance ratios may need focused intervention on a single grammar point; students with high overcorrection ratios may not be reliably assessed by the current pipeline.

*Variables:* Error rate, dominance ratio, overcorrection ratio (continuous, thresholded at 2σ per cohort).

---

### RQ12 [Individual — Feedback accuracy]

**To what extent does the AI-generated summary feedback align with the quantitative error-type distribution for each student, and which error types are systematically under-represented or over-represented in the qualitative feedback text?**

*Approach:* For a sample of 20–30 files, extract the error types mentioned in the `summary` text (via keyword matching against ERRANT code descriptions and human-readable labels). Compare against the actual top-5 error types from `errant_analysis.errors`. Compute precision and recall: of the errors the summary mentions, how many are in the student's actual top-5? Of the student's actual top-5, how many appear in the summary? Identify systematic patterns — e.g., does the LLM over-emphasise spelling errors (which are visible and easy to describe) while under-emphasising determiner errors (which are subtle)?

*Variables:* Error types in AI summary (predicted set); error types in quantitative top-5 (ground truth set); precision, recall per error type.

---

### RQ13 [Methodology — Majority-voting reliability]

**To what extent does the dual-temperature majority-voting mechanism produce divergent edit annotations between passes, and are certain grammatical error types disproportionately affected by inter-pass annotation disagreement?**

*Approach:* Track `metadata.uncertain_edit_count` as a proportion of `metadata.total_edit_count`. Compute the cohort-wide mean uncertainty ratio. Break down uncertainty by error type where edit-level data permits (requires examining the raw edit lists before majority-vote filtering, which is metadata held in `intersect_edits` logic). If certain error types (e.g., R:WO, R:OTHER) consistently show higher disagreement between temperature passes, this indicates areas where the correction model is unreliable and results should be interpreted cautiously.

*Variables:* Temperature pass (2 levels); edit agreement/disagreement per error type; uncertainty ratio.

---

### RQ14 [Methodology — Edit span and error type]

**What is the relationship between edit span (number of tokens affected by a correction) and error type classification, and do multi-token edits correlate with elevated overcorrection rates?**

*Approach:* `metadata.edit_width_stats` records `max_span`, `avg_span`, and `multi_token_edits` per file. Correlate these with per-file overcorrection rate. At the error-type level (where feasible from edit-level metadata), test whether morphological errors (R:MORPH, R:SPELL) produce narrower edits than syntactic errors (R:WO, R:VERB:TENSE). Wide multi-token edits combined with high overcorrection would suggest the model is performing wholesale rewriting rather than minimal-edit correction — a known failure mode in LLM-based GEC.

*Variables:* Edit span (continuous, from metadata); error type (categorical); overcorrection rate (continuous).

---

## Research Questions by Data Requirement

| Question | Data needed | Complexity | Feasibility |
|----------|-------------|------------|-------------|
| RQ1 | `errant_analysis.errors`, `class`, `word_count` | Low | Immediate |
| RQ2 | `error_rate`, `class`, `student_id` | Low | Immediate |
| RQ3 | `errant_analysis.errors`, `class`, `word_count` | Medium | Immediate (stats) |
| RQ4 | All research files + `submission_date` | Medium | **Strong** (70 students with 2-15 submissions) |
| RQ5 | `metadata.*`, `error_rate`, `submission_date` | Medium | Immediate |
| RQ6 | `topic`, `errant_analysis.errors`, `class` | Medium | Needs topic inventory (V8) |
| RQ7 | Cross-ref with `docs/students.txt` for sub-class | Medium | **Constrained to active group only (36 students, 2 sub-classes)** |
| RQ8 | `word_count`, `error_rate`, `class` | Low | Immediate |
| RQ9 | `errant_analysis.uncategorised`, `metadata.total_edit_count` | Medium | Immediate |
| RQ10 | `errant_analysis.errors`, `student_id`, `word_count` | High | Needs clustering libs |
| RQ11 | `error_rate`, `errant_analysis.errors`, `metadata.*` | Medium | Immediate |
| RQ12 | `summary`, `errant_analysis.errors` | Medium | Needs NLP/text parsing |
| RQ13 | `metadata.uncertain_edit_count`, `metadata.total_edit_count` | Low | Immediate |
| RQ14 | `metadata.edit_width_stats`, `metadata.overcorrection_count` | Low | Immediate |

---

## Implementation Phases

### Phase 1: Data Extraction and Wrangling

**Step 1.1 — Extraction:** Build `src/interpret_results.py`:
1. Iterate all `local-working/research-*.json`
2. Extract: `student_id`, `class`, `name`, `error_rate`, `word_count`, `errant_analysis.errors[]`, `errant_analysis.uncategorised`, `metadata` (overcorrection_count, total_edit_count, uncertain_edit_count, edit_width_stats), `topic`, `submission_date`, `summary`
3. Cross-reference with `docs/students.txt` to recover sub-class assignments
4. Aggregate into pandas DataFrames (one per cohort, one combined)
5. Normalise error counts to errors-per-100-words for cross-student comparison
6. Output clean summary CSVs for further analysis

**Step 1.2 — Data Validation Gate:** Run all 8 validation checks (V1–V8 from the Data Validation Plan above) against the extracted data. Validation must pass with documented exceptions before any analysis begins:
- V1–V3 (automatic): Completeness, structure, and range checks run as assertions in the extraction script
- V4–V6 (cross-reference): Cohort assignment, duplicate detection, date consistency — run after DataFrame assembly
- V7 (consistency): Error count delta check — run after normalisation
- V8 (standardisation): Topic field — requires manual review of unique values before RQ6 proceeds
- **Gate rule:** If ≥5% of files fail any single validation check, halt and investigate the pipeline before proceeding. Lower failure rates are documented in an exclusions appendix and excluded on a per-check basis

### Phase 2: Desk Statistics (RQ1–RQ3, per Statistical Analysis Plan)
- **RQ1:** Ranked error-type frequency tables, grouped bar charts (M2 vs M3 per error type), per-100-words normalised rates
- **RQ2:** Per-cohort cumulative error-rate CDF plots with threshold markers at 10%, 15%, 20%, 25%; dual-histogram with overlaid density
- **RQ3:** Mann-Whitney U tests per error type (Bonferroni-corrected α); Cliff's delta effect sizes; differential heatmap (M2-dominant vs M3-dominant error types)

### Phase 3: Core Analysis (RQ4–RQ9, RQ11, RQ13–RQ14, per Statistical Analysis Plan)
- **RQ4:** Per-student error_rate slopes over submission_number; χ² test comparing improvement rates between active/former groups; per-type trajectory profiles (top-10 errors); optional mixed-effects model; spaghetti plots with cohort LOESS overlay
- **RQ5:** Per-student overcorrection_ratio trajectories (sign test for trend); Mann-Whitney U comparing active vs former groups; Spearman correlations with error_rate and multi_token_edits
- **RQ6:** Kruskal-Wallis per error type across topic categories (post-hoc Dunn's with Bonferroni); topic × error-type heatmap; χ² topic-distribution test between cohorts
- **RQ7:** Mann-Whitney U comparing M3-4A vs M3-5A within active group; Cliff's δ effect sizes; sub-class boxplots
- **RQ8:** Spearman's ρ between word_count and error_rate by cohort; Fisher's z for between-cohort moderation; LOESS-smoothed scatterplots
- **RQ9:** Uncategorised-edit ratio histogram; correlations with error_rate and overcorrection_count; qualitative sample of 20 uncategorised pairs
- **RQ11:** 2σ outlier detection on error rate, dominance ratio, and overcorrection_ratio; flagged-student table with summary excerpts
- **RQ13:** Uncertainty-ratio histogram and Spearman correlation with error_rate; per-type disagreement rates (if edit-level metadata is made available)
- **RQ14:** Spearman's ρ between edit span metrics and overcorrection_count; per-type edit span comparison (if per-type span data is made available)

### Phase 4: Advanced Analysis (RQ10, RQ12, per Statistical Analysis Plan)
- **RQ10:** PCA (≥80% variance explained) + k-means clustering (k=2–6, elbow + silhouette selection); hierarchical clustering for consensus; t-SNE visualisation; cluster stability via bootstrap Adjusted Rand Index
- **RQ12:** Regex-based error-type extraction from `summary` field on stratified sample (40 files); per-student precision/recall/F1; per-type over/under-representation rates; Wilcoxon signed-rank for precision vs recall asymmetry

### Phase 5: Report Generation
- Feed findings into the existing Typst report pipeline (`/local-report`)
- Produce structured output: executive summary, desk statistics, detailed analysis by research question, data quality appendix

---

## Statistical Analysis Plan

All analyses use Python with `scipy`, `statsmodels`, `scikit-learn`, and `pandas`. Significance threshold α = 0.05 throughout. Where multiple comparisons are made, apply Bonferroni correction: adjusted α = 0.05 / k, where k is the number of independent tests.

### RQ1 — Error frequency rankings (descriptive)

- Aggregate per-cohort error-type totals and normalise to errors per 100 words
- Report absolute counts and normalised rates in a ranked table
- Visual: grouped horizontal bar chart, top-15 error types, with M2 and M3 side-by-side
- No inferential test needed; this is descriptive census of the known population (all available submissions)

### RQ2 — Error-rate thresholding (descriptive)

- Compute per-student mean error rate (across all their submissions)
- Bin students into ≤10%, 10–15%, 15–20%, 20–25%, >25%
- Report proportion in each bin for M2 and M3 separately
- Visual: dual-histogram or kernel density plot with threshold lines overlaid; cumulative distribution function (CDF) plot
- No inferential test; thresholds are diagnostic benchmarks, not hypothesis tests

### RQ3 — Between-cohort error-type divergence (inferential)

- **Test:** Two-sample Mann-Whitney U (Wilcoxon rank-sum) per error type, comparing active (M2 label) vs former (M3 label) students, on normalised error counts (errors/100 words)
- **Why non-parametric:** Error-type counts are zero-inflated and right-skewed; most students have zero for many error types. Mann-Whitney does not assume normality and is robust to outliers
- **Multiple comparison correction:** Bonferroni across k error types actually tested. Compute per-type only for error types present in ≥10% of files to avoid testing near-zero denominators
- **Effect size:** Cliff's delta (δ) — a non-parametric effect size. Interpretation: |δ| < 0.147 negligible, 0.147–0.33 small, 0.33–0.474 medium, ≥0.474 large
- **Assumptions check:** Verify homogeneity of distribution shape between groups via visual inspection of histograms. If shapes differ severely, supplement with Brunner-Munzel test
- **Output:** Table of error types ranked by Cliff's δ magnitude, with p-values (adjusted), and whether each type is dominant in active or former group

### RQ4 — Longitudinal trajectories (inferential, n=70)

- Per-student slope of error_rate over submission_number (linear regression or loess). Classify each student as improving (negative slope, p<0.10), stable, or regressing (positive slope, p<0.10)
- χ² test comparing proportions of improving/stable/regressing between active and former groups
- Per-error-type trajectories: aggregate slopes across students for the top-10 most common error types. Classify each type as "commonly resolving" (≥50% of students negative slope), "persistent" (<25% negative slope), or "mixed"
- Optional mixed-effects model: `error_rate ~ submission_number * group + (1 | student_id)` using `statsmodels` or `lme4` via `statsmodels.formula.api`
- Visual: small-multiples spaghetti plots per student (thin grey lines) with cohort-level LOESS smooth overlaid in colour
- No formal power analysis needed; this is a census (all available students), not a sample

### RQ5 — Overcorrection stability (longitudinal + correlational)

- **Within-student trajectory:** Plot `overcorrection_ratio` against `submission_number` for each student with ≥5 submissions. Compute per-student slope. Test proportion with positive slope (overcorrection worsening over time) via sign test
- **Group comparison:** Mann-Whitney U comparing mean `overcorrection_ratio` between active (M2) and former (M3) groups. If former students have higher ratios, model reliability may be worse for the students who later left
- **Cross-sectional correlations:** Spearman's ρ between `overcorrection_ratio` and (a) `error_rate`, (b) `multi_token_edits`. Tests whether the correction model is least reliable for high-error students and whether multi-token edits are reliable signals of overreach
- **Assumptions:** Spearman is rank-based. No normality assumption. Outliers checked via scatterplot
- **Output:** Per-student overcorrection trajectory plots; group comparison boxplot; ρ coefficients with 95% CI

### RQ6 — Topic sensitivity (inferential + descriptive)

- **Step 1 — Topic inventory:** Extract all unique `topic` values. Manually group into categories (narrative, argumentative, transactional/email, descriptive, mixed)
- **Step 2 — Descriptive:** Per-topic error-type profiles, normalised per 100 words, as a heatmap (topics × error types)
- **Step 3 — Inferential:** Kruskal-Wallis test per error type across topic categories, controlling for cohort. Post-hoc Dunn's test with Bonferroni correction if Kruskal-Wallis is significant
- **Confound check:** Test whether topic distribution differs between M2 and M3 using χ² test of independence. If significant, RQ3 results may be partially confounded by topic
- **Assumptions:** Kruskal-Wallis: independent samples, ordinal/continuous DV, similar distribution shape across groups. Dunn's test as robust post-hoc

### RQ7 — Sub-class effects (inferential, within active group only)

- **Step 1 — Cross-reference:** Join research files with `docs/students.txt` on `student_id` to recover sub-class (M3-4A or M3-5A). Only the 36 active (M2-labelled) students are in students.txt; former students have no sub-class assignment and are excluded
- **Step 2 — Error rate:** Mann-Whitney U comparing per-student mean error rate between M3-4A and M3-5A (two-group comparison, no need for ANOVA)
- **Step 3 — Error-type profiles:** Separate Mann-Whitney U tests per error type with Bonferroni correction, on normalised counts
- **Assumptions:** Mann-Whitney is non-parametric, no normality assumption. Distributions checked visually for shape similarity
- **Confound check:** χ² test for topic distribution across M3-4A and M3-5A. If significant, RQ7 differences may be topic-driven rather than instruction-driven
- **Power warning:** n=18 per sub-class. Differences need to be large (Cliff's δ > 0.5) to reach significance at α=0.05. Report effect sizes regardless of p-values
- **Output:** Table of per-sub-class means with Cliff's δ; boxplots of mean error rate per sub-class

### RQ8 — Word-count vs error-rate relationship (correlational, inferential)

- **Test:** Spearman's ρ between `word_count` and `error_rate`, computed per cohort and combined
- **Moderation test:** Fisher's z-transformation to test whether ρ differs significantly between M2 and M3
- **Assumptions:** Spearman is robust to non-linearity and outliers. Visual inspection of scatterplot to confirm monotonic relationship (if U-shaped, Spearman will miss it — verify via LOESS line)
- **Output:** Scatterplot with LOESS smooth per cohort; ρ coefficients with 95% CI; Fisher's z test result

### RQ9 — Uncategorised errors (descriptive + qualitative)

- **Step 1 — Prevalence:** Compute for each file: uncategorised_ratio = len(`uncategorised`) / `metadata.total_edit_count`. Report mean and median per cohort. Histogram of ratios
- **Step 2 — Correlates:** Spearman correlation between uncategorised_ratio and `error_rate`, `overcorrection_count`, `multi_token_edits`
- **Step 3 — Qualitative:** Random sample of 20 uncategorised edit pairs. Manually label linguistic phenomena: L1-transfer, idiom, discourse reformulation, model hallucination, genuine ERRANT taxonomy gap
- No formal inferential test for the qualitative step; theme-frequency reporting

### RQ10 — Error-profile clustering (unsupervised ML)

- **Feature engineering:** Per-student vector of normalised error-type counts (errors/100 words). Impute zeros for error types absent in a student's file
- **Dimensionality reduction:** PCA (standardise features first). Retain components explaining ≥80% cumulative variance. Visual: PCA biplot with top-loading error types labelled
- **Clustering algorithm:** k-means (k=2 through k=6). Determine optimal k via elbow method (inertia plot) and silhouette score
- **Alternative algorithm:** Test hierarchical clustering (Ward's method) with Euclidean distance on PCA-reduced features. Compare dendrogram cut-points to k-means solutions for consensus
- **Visualisation:** t-SNE plot (perplexity tuned to 5–30 range) colour-coded by cluster assignment
- **Interpretation:** Per-cluster mean error-type profile as a radar chart / parallel coordinates plot. Assign descriptive labels to each cluster
- **Validation:** Silhouette scores; cluster stability via bootstrap resampling (repeat clustering on 80% subsamples, compute Adjusted Rand Index between subsample solutions)

### RQ11 — Outlier detection (threshold-based)

- **Three metrics per student:** (1) mean error rate, (2) dominance ratio (count of most-frequent error type / total errors, undefined if zero errors — set to 0), (3) overcorrection_ratio = `overcorrection_count` / `total_edit_count`
- **Threshold:** 2σ above cohort mean (or above 95th percentile if distributions are non-normal). Apply per cohort
- **Triangulation:** Flag if a student exceeds 2σ on at least one metric. Cross-reference flagged students against their `summary` text for qualitative verification
- **Output:** Table of flagged students with metrics, cohort, and summary excerpt; scatterplot of error rate vs dominance ratio with flagged points highlighted

### RQ12 — LLM feedback accuracy (classification evaluation)

- **Sample:** 20 files per cohort (40 total), stratified by error rate quintile to ensure representative coverage
- **Ground truth extraction:** Parse `summary` text using regex matching against the 55 ERRANT code descriptions + human-readable names from `ERRANT_CODE_NAMES`. Extract the set of error types *mentioned* in the summary
- **Metrics per student:** Precision = (mentioned ∩ actual_top5) / |mentioned|, Recall = (mentioned ∩ actual_top5) / |actual_top5|, F1
- **Per-type analysis:** Compute the proportion of students for whom each error type appears in the top-5 but is *not* mentioned in the summary (under-representation rate), and vice versa (over-representation rate)
- **Statistical test:** Wilcoxon signed-rank test comparing precision vs recall across the sample — tests whether the LLM systematically over- or under-reports
- **Output:** Per-student precision/recall table; bar chart of over/under-representation rate per error type

### RQ13 — Majority-voting reliability (descriptive + correlational)

- **Metric:** uncertainty_ratio = `metadata.uncertain_edit_count` / `metadata.total_edit_count`
- **Descriptive:** Mean and median uncertainty ratio per cohort. Histogram
- **Correlational (cross-sectional):** Spearman's ρ between uncertainty_ratio and error_rate. Tests whether harder-to-correct students are also less reliably annotated
- **Error-type breakdown (if metadata available):** The current pipeline stores `uncertain_edit_count` only at the file level, not per error type. If the raw edit lists from `intersect_edits()` can be accessed (modifying `errant_analysis.py` to persist them), compute per-type disagreement rates. Otherwise, report this as a limitation
- **Output:** Uncertainty ratio distribution per cohort; scatterplot vs error rate

### RQ14 — Edit span analysis (correlational + comparative)

- **Metric:** per-file `max_span`, `avg_span`, `multi_token_edits` from `metadata.edit_width_stats`
- **RQ14a (correlational):** Spearman's ρ between edit span metrics and `overcorrection_count`. Hypothesis: wider edits → more overcorrection (model rewrites rather than minimally edits)
- **RQ14b (comparative — if per-type edit span available):** If the pipeline is extended to log edit spans per error type, test via Kruskal-Wallis whether morphological errors (R:SPELL, R:MORPH, R:NOUN:NUM) produce narrower edits than syntactic errors (R:WO, R:VERB:TENSE, R:CONJ). Otherwise, report as limitation
- **Output:** Scatterplot of multi_token_edits vs overcorrection_count; per-type edit span boxplots (if data available)

---

## Data Validation Plan

Data validation runs as a pre-analysis gate in Phase 1 (data wrangling). No analysis proceeds on unvalidated data.

### V1. File-level completeness check

- **Check:** For each of the 689 files, verify presence of required fields: `student_id`, `class`, `error_rate`, `word_count`, `errant_analysis`, `metadata`
- **Action on failure:** Log missing-field count per file. If >5% of files lack a field, that field is excluded from any analysis requiring it. If a single file lacks critical fields (`student_id`, `class`, `error_rate`), exclude it and log to exclusions report
- **Output:** Completeness report — field × % present

### V2. Structural integrity check

- **Check for `errant_analysis.errors`:** Verify this is a list with entries containing `type`, `count`, and `example` keys. If `count` is non-integer or negative, flag
- **Check for `errant_analysis.uncategorised`:** Verify it is a list. Log length
- **Check for `metadata` sub-fields:** Verify `total_edit_count`, `overcorrection_count`, `uncertain_edit_count` are present and non-negative integers; `edit_width_stats` dict exists with `max_span`, `avg_span`, `multi_token_edits`
- **Action on failure:** Flag specific files for manual inspection. Exclude from affected analysis if structure is corrupted

### V3. Value range checks

- `error_rate`: must be 0–100. Flag if <0 or >100 (indicates data pipeline error)
- `word_count`: must be ≥1. Flag if 0 (should have been excluded by `process_file()` but verify)
- `overcorrection_count` ≤ `total_edit_count`. Flag if violated (logical impossibility)
- `uncertain_edit_count` ≤ `total_edit_count`. Flag if violated
- `total_edit_count` ≥ 0. Flag if negative
- **Action on failure:** Flagged files are investigated in a batch report. Obvious pipeline errors (e.g., error_rate = 500%) are excluded. Edge cases (error_rate = 0, word_count = 5) are retained but noted

### V4. Cohort assignment verification

- **Check:** Cross-reference every `student_id` in research files against `docs/students.txt`. Verify:
  - Every student_id exists in students.txt (if not, flag as orphan)
  - The `class` field (M2/M3) in the research file is consistent with the class prefix in students.txt (e.g., student 29561 in research file has class="M2" but students.txt says M3-4A)
- **Action on failure:** If class mismatch detected, prefer students.txt (source of truth) and log discrepancy. If student not in students.txt, retain at cohort level if `class` field is present; exclude from RQ7 (sub-class analysis) but include in broader analyses
- **Output:** Mismatch report — student_id, class_in_file, class_in_students_txt, action_taken

### V5. Duplicate detection

- **Check:** Are there multiple research files for the same `student_id`? (Expected: yes, for some students; this is not an error)
- **Distinguish** intentional duplicates (same student, different record_id — longitudinal data) from true duplicates (same student_id + same word_count + same error_rate — likely a re-run artifact)
- **Action on failure:** True duplicates: keep the first (or most complete) and exclude the rest. Log both cases, counts, and file names
- **Output:** Duplicate report — per-student file counts, flagged true duplicates

### V6. Submission date consistency

- **Check:** For files with `submission_date`, verify ISO 8601 or parseable format. Identify date range (min/max). Flag dates outside calendar year 2025–2026
- **Check:** For multi-submission students in historical_data.json, verify chronological ordering (submission dates should not decrease)
- **Action on failure:** Unparseable dates are excluded from temporal analyses (RQ4, RQ5) but retained for other analyses. Chronological inversions are flagged for manual investigation
- **Output:** Date range summary; per-student date sequence reports (longitudinal students only)

### V7. Error count vs total_edit_count consistency

- **Code logic:** `classify_edits()` in `errant_analysis.py` (line 583) explicitly skips edits with type `"UNK"` or `"U:SPACE"` — they are NOT added to the `errors` list. They ARE, however, counted in `total_edit_count` (derived from `len(edits)` before filtering). So the expected accounting is:
  - `total_edit_count` = sum of errors[i].count + len(uncategorised) + count(UNK drops) + count(U:SPACE drops)
- **Check:** Compute per-file: `delta = total_edit_count - sum(errors[i].count) - len(uncategorised)`. The delta should be small (ideally ≤ 5), representing the sum of UNK + U:SPACE drops.
- **Audit finding:** Across all 689 files, 481 have delta = 0, 199 have delta between -4 and -1 (small discrepancies likely from rounding or duplicate counting). **However, 5 files have massive deltas of 81, 90, 161, 228, and 332** — indicating that a large number of edits were silently dropped. These files require individual investigation:
  - Are these particular students with unusual language features?
  - Are these files from the same correction run (same batch)?
  - Do these high-delta files cluster in one cohort?
  - If the dropped edits are systematic (e.g., all U:SPACE), the error-type analysis may underestimate certain error categories for these students.
- **Action on failure:** Files with |delta| ≥ 5 are flagged for manual inspection. If high-delta files cluster within a single student, that student is excluded from error-type-level analyses (RQ3, RQ6, RQ10, RQ12) but retained for file-level analyses (RQ2, RQ8). An appendix documents the nature of dropped edits for each flagged file.
- **Output:** Delta distribution histogram; flagged file list with investigation results.

### V8. Topic field standardisation

- **Check:** Extract all unique `topic` values. Identify near-duplicates (e.g., "mobile phones in class" vs "Should mobile phones be allowed?") via Levenshtein distance clustering
- **Action:** Manual review of unique topic values; merge near-duplicates into canonical labels. Files with missing `topic` are excluded from RQ6 but retained for other analyses
- **Output:** Topic inventory table — raw_value, canonical_label, file_count

### V9. Historical_data deduplication

- **Check:** `local-working/historical_data.json` contains 19 entries but only 10 unique (`student_id`, `submission_date`, `error_percent`) combinations. The 9 extras are exact duplicates.
- **Action:** Deduplicate to 10 unique entries (3 students × 3 submissions + 1 summary row). Verify chronological ordering within each student.
- **Note:** `historical_data.json` is a secondary data source for RQ4 contextualisation only. The primary longitudinal data lives in the individual research JSON files, which are not affected by this duplication.
- **Output:** Cleaned historical_data.json (10 entries).

---

## Data Quality Caveats

1. **Class-label convention**: The `class` field in research files does NOT indicate academic year level (M2 vs M3). It indicates enrollment status: **M2 = currently enrolled** (student ID found in classlist), **M3 = left the program** (student ID not found in classlist). All 36 active students are from academic levels M3-4A and M3-5A in the paper classlist but are labelled M2 because they're still enrolled. This convention is intentional and consistent (zero anomalies across 689 files) but must be clearly communicated when presenting results.

2. **Sentence pair alignment**: `sentence_pairs` in sampled files showed misalignment (short originals matched to long corrected sentences). This field should not form the basis of analysis without prior validation of the `align_sentences()` output.

3. **Field completeness**: 9 files (1.3%) lack `submission_date`, 9 lack `topic`, and 8 have empty `record_id` (defaulting to "?"). Exclude or impute as appropriate on a per-question basis. The 680 files with dates have 398 unique dates — excellent granularity for longitudinal analysis.

4. **Historical_data duplicates**: `historical_data.json` has 9 duplicate entries (19 rows → 10 unique). Deduplication is straightforward and does not affect the primary research files.

5. **Overcorrection interpretation**: Elevated `overcorrection_count` may reflect either genuine multi-word errors or model overreach. Interpret alongside edit-width metadata (RQ14) and validate with between-pass uncertainty ratio (RQ13).

6. **Majority-voting metadata**: `metadata.uncertain_edit_count` captures inter-pass divergence at the per-file level. Error-type-level uncertainty breakdowns (deeper RQ13) may require access to raw edit lists pre-filtering, which the current pipeline does not persist to JSON.

7. **High-delta files (V7)**: 5 files have total_edit_count far exceeding the sum of classified errors (delta 81–332). These appear to have large numbers of silently dropped UNK/U:SPACE edits. Until these files are investigated, they should be excluded from any analysis that depends on error-type-level data.
