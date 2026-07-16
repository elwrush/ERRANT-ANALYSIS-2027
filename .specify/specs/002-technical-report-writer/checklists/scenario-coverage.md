# Scenario Coverage Checklist — Technical Report Writer

Checks whether all user flows and system scenarios are addressed in the requirements.

- [ ] CHK047 Is the happy-path scenario covered? — User provides valid data path + title + no custom sections → report generated with 11 baseline sections. [§FR-001, FR-002, FR-004]
- [ ] CHK048 Is the custom-sections scenario covered? — User provides valid data + title + 1–5 custom sections with rhetorical questions → report includes additional sections at correct insertion points. [§FR-003]
- [ ] CHK049 Is the review-gate sign-off scenario covered? — User receives Markdown draft, reviews, types "proceed" → PDF generated. [§FR-010]
- [ ] CHK050 Is the review-gate revision scenario covered? — User requests changes to draft → agent revises and re-presents. [§Edge Cases "User cancels"]
- [ ] CHK051 Is the review-gate cancel scenario covered? — User cancels → draft saved with "DRAFT — not signed off". [§Edge Cases]
- [ ] CHK052 Is the empty-data-directory scenario covered? — Invalid data path → error message: "No JSON files found at <path>". [§Edge Cases]
- [ ] CHK053 Is the partial-validation-failure scenario covered? — Some JSONs valid, some invalid → log per-file errors, offer skip or abort. [§Edge Cases]
- [ ] CHK054 Is the single-student scenario covered? — One JSON in data → summary table instead of charts, limitation noted. [§Edge Cases, §C-003]
- [ ] CHK055 Is the single-cohort scenario covered? — All students same cohort → no cohort comparison chart, table used instead. [§C-003]
- [ ] CHK056 Is the no-errors scenario covered? — All students have error_rate = 0 → error_code_summary empty, note in report. [§C-002]
- [ ] CHK057 Is the Tavily-unavailable scenario covered? — Tavily API fails → fallback to default style guide, log warning. [§Edge Cases]
- [ ] CHK058 Is the Playwright-unavailable scenario covered? — Playwright not installed → error message with install instructions. [§C-004 contract tests]
- [ ] CHK059 Is the title-sanitisation scenario covered? — Special characters in title → stripped, safe filename generated. [§Edge Cases]
- [ ] CHK060 Is the insertion-point-conflict scenario covered? — Two custom sections at same position → ask user to re-specify. [§Edge Cases]
- [ ] CHK061 Is the header-template-missing scenario covered? — WRITING_ASSESSMENT_NEW header files not found → minimal fallback header. [§Edge Cases]
- [ ] CHK062 Is the word-count-too-low scenario covered? — Students with <40 words flagged but included. [§data-model.md]
