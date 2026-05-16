# Sampling Methodology for Writing Error Analysis

## 1. Research Context

This document describes the sampling methodology used to select student writing submissions for grammatical error analysis (ERRANT). The corpus consists of handwritten essays transcribed via OCR (Gemini 2.5 Flash Lite) and stored in a Supabase `student_submissions` table. Each row represents a single essay submission by a student and includes a `skill` field identifying the language skill assessed (Writing, Speaking, Reading, Listening, Use of English).

This analysis targets only **Writing** submissions. The total corpus contains 978 Writing records contributed by 97 distinct students.

## 2. Cohort Assignment

Students are assigned to one of two cohorts based on academic year progression. The `classlists` table contains students enrolled in the current academic year, alongside their current class level. The mapping logic follows the school's year-on-year progression:

- **M2 cohort**: Students currently enrolled in M3 classes (M3-4A, M3-5A). These students submitted their writing when they were in M2 the previous academic year. Their submissions therefore represent M2-level writing ability.
- **M3 cohort**: Students who appear in `student_submissions` but are **absent** from the current `classlists`. These students have graduated or left the programme; their submissions represent M3-level writing ability.

Current M2 students (M2-4A, M2-5A) and current M3-3A students do not appear in the Writing submissions and are excluded from this analysis.

### 2.1 Cohort Sizes

| Cohort | Students | Writing Records | Records per Student |
|--------|----------|-----------------|-------------------|
| M2 | 36 | 289 | 8.0 |
| M3 | 61 | 689 | 11.3 |
| **Total** | **97** | **978** | **10.1** |

## 3. Sampling Unit and Pseudoreplication

A central methodological concern in learner corpus research is **pseudoreplication** arising from multiple texts per learner. Gries (2021) demonstrates that learner corpus data frequently suffers from *dispersion* problems: linguistic features and error types are often "clumpily distributed" across speakers, meaning that a small minority of learners may contribute the majority of occurrences of a given error type. When individual texts (rather than learners) are treated as independent observations, type I error rates are inflated and confidence intervals are spuriously narrow.

Larson-Hall and Herrington (2009) and Paquot and Plonsky (2017) further show that second language acquisition research is often underpowered precisely because clustering effects are ignored. Learner Corpus Research (LCR) guidelines therefore consistently recommend treating the **learner as the sampling unit** (Gries 2021, Paquot & Plonsky 2017, Caines & Buttery 2017).

**Decision**: The student is treated as the sampling unit. All records from a selected student are included in the sample; no record-level selection is performed within students.

## 4. Sample Size Determination

### 4.1 Statistical Framework

Sample size requirements are calculated using Cochran's formula for proportions with finite population correction (Cochran 1977):

$$n_0 = \frac{Z^2 \cdot p \cdot (1-p)}{E^2}$$

$$n = \frac{n_0}{1 + \frac{n_0 - 1}{N}}$$

Where:
- $Z = 1.96$ (95% confidence level)
- $p = 0.5$ (maximum variance assumption for a proportion)
- $E$ = desired margin of error
- $N$ = population size
- $n$ = required sample size

### 4.2 Required Sample Sizes by Precision Level

| Margin of Error | M2 (N=289) | M3 (N=689) |
|----------------|------------|------------|
| ±3% | 228 (79%) | 419 (61%) |
| ±5% | 166 (57%) | 247 (36%) |
| ±8% | 99 (34%) | 124 (18%) |
| ±10% | 73 (25%) | 85 (12%) |

### 4.3 Published Benchmarks

The sample sizes recommended here are consistent with published learner corpus studies:

- Nebrija Learner Corpus: 36 texts, 5,908 words — a published error analysis at this scale (Fernández 2012).
- NUS Corpus of Learner English (NUCLE): 1,400 essays, 1.2 million words, 46,597 annotated errors (Dahlmeier et al. 2013).
- Cambridge Learner Corpus subcorpora: 161,000–449,000 words per CEFR level per L1 group used in published agreement error analysis (Balçıkanlı & Çakır 2018).
- LONGDALE corpus: up to 3 measurement points per learner across 3 academic years (Paquot et al. 2013).
- Turkish subcorpus of CLC: 512,052 words. Greek subcorpus: 1,329,458 words (Balçıkanlı & Çakır 2018).
- CLC total error-coded component: 6 million words across 86 L1 backgrounds (Nicholls 2003).

For the cohort-level student populations (36 and 61 students), Tipton et al. (2017) note that samples of 10–70 sites in education research can support descriptive generalization but caution that "sharp inferences to large populations from small experiments are difficult even with probability sampling." Neumann (2007) gives a rule of thumb of ~300 samples for populations under 1,000 in social sciences, which the combined corpus comfortably exceeds.

### 4.4 Clustering Adjustment

Because the effective sample size is reduced by within-student correlation of errors, a design effect correction is warranted (Kish 1965):

$$n_{eff} = \frac{n}{1 + \rho \cdot (m - 1)}$$

Where $\rho$ is the intraclass correlation coefficient for error rates within students and $m$ is the average number of records per student. For plausible $\rho$ values of 0.2–0.4 in learner writing (Caines & Buttery 2017), the effective sample sizes for M2 and M3 are:

| Cohort | $n_{students}$ | Records | $n_{eff}$ ($\rho=0.3$) |
|--------|---------------|---------|----------------------|
| M2 | 36 | 289 | ~87 |
| M3 (full) | 61 | 689 | ~118 |
| M3 (sampled) | 36 | 396 | ~86 |

These effective sample sizes remain above the 20–30 student minimum threshold identified across published learner corpus studies (Fernández 2012; Caines & Buttery 2017).

## 5. Sampling Strategy

### 5.1 Approach

**M2 cohort**: **All 36 students (289 records) are included** with no sub-sampling. With 36 students, this is a small population for which sampling would incur information loss disproportionate to any efficiency gain (Cochran 1977 recommends full enumeration when the sampling fraction exceeds 50%).

**M3 cohort**: **36 students are randomly selected** from the 61 available, yielding an estimated ~396 records. The sample size is matched to the M2 cohort count to enable balanced cohort comparison — a design that avoids the statistical power asymmetry of unequal groups (Cohen 1988, 1992).

### 5.2 Method

Selection is performed using simple random sampling without replacement at the student level. A fixed random seed (42) is used to ensure reproducibility. The selected student IDs and all their associated records constitute the analysis sample.

### 5.3 Resulting Sample

| Cohort | Sampled Students | Sampled Records | Fraction of Cohort |
|--------|-----------------|-----------------|-------------------|
| M2 | 36 | 289 | 100% (full) |
| M3 | 36 | 396 | 59% of students, ~57% of records |
| **Total** | **72** | **685** | 70% of all students |

## 6. Limitations and Caveats

1. **M2 population size (36 students)** is at the lower bound for inferential statistics. Descriptive statistics (error type frequencies, rates per 100 words) are appropriate; inferential comparisons between cohorts should be interpreted with caution (Tipton et al. 2017).

2. **The matched-sample design (36 vs 36)** prioritises balanced comparison over full M3 coverage. If characterising M3 independently is the primary goal, all 61 students should be included.

3. **Intraclass correlation** of errors within students is assumed but not measured in the current dataset. Future analysis should calculate $\rho$ for each error type and adjust effective sample sizes accordingly (Kish 1965).

4. **Convenience sampling** constrains generalisation to the broader population of L2 learners. The corpus represents one school in Thailand and generalisability to other contexts requires replication (Neumann 2007).

## References

Balçıkanlı, C., & Çakır, İ. (2018). Agreement errors in learner corpora across CEFR. *European Journal of English Language Teaching*, 3(4), 83–102.

Caines, A., & Buttery, P. (2017). The effect of task and topic on opportunity of use in learner corpora. *International Journal of Learner Corpus Research*, 3(1), 35–60.

Cochran, W. G. (1977). *Sampling techniques* (3rd ed.). John Wiley & Sons.

Cohen, J. (1988). *Statistical power analysis for the behavioral sciences* (2nd ed.). Lawrence Erlbaum Associates.

Cohen, J. (1992). A power primer. *Psychological Bulletin*, 112(1), 155–159.

Dahlmeier, D., Ng, H. T., & Wu, S. M. (2013). Building a large annotated corpus of learner English: The NUS Corpus of Learner English. *Proceedings of the 8th Workshop on Innovative Use of NLP for Building Educational Applications*, 22–31.

Fernández, M. P. (2012). A corpus-based analysis of errors in adult EFL writings. *Revista de Lingüística y Lenguas Aplicadas*, 7, 207–218.

Gries, S. Th. (2021). Statistical analyses of learner corpus data. In N. Tracy-Ventura & M. Paquot (Eds.), *The Routledge handbook of SLA and corpora* (pp. 118–134). Routledge.

Kish, L. (1965). *Survey sampling*. John Wiley & Sons.

Krejcie, R. V., & Morgan, D. W. (1970). Determining sample size for research activities. *Educational and Psychological Measurement*, 30(3), 607–610.

Larson-Hall, J., & Herrington, R. (2009). Improving data analysis in second language acquisition by utilizing modern developments in applied statistics. *Applied Linguistics*, 31(3), 368–390.

Neumann, W. L. (2007). *Social research methods: Qualitative and quantitative approaches* (6th ed.). Pearson.

Nicholls, D. (2003). The Cambridge Learner Corpus: Error coding and analysis for ELT. *Proceedings of the Corpus Linguistics 2003 Conference*, 572–581.

Paquot, M., & Plonsky, L. (2017). Quantitative research methods and study quality in learner corpus research. *International Journal of Learner Corpus Research*, 3(1), 61–94.

Tipton, E., Hallberg, K., Hedges, L. V., & Chan, W. (2017). Implications of small samples for generalization: Adjustments and rules of thumb. *Evaluation Review*, 41(5), 472–505.
