# Edge Case Coverage Checklist — Technical Report Writer

Checks whether boundary conditions and unusual inputs are defined in the requirements.

- [ ] CHK063 Is the empty data directory case defined? — Expected: clear error, no crash. [§Edge Cases]
- [ ] CHK064 Is the all-JSONs-invalid case defined? — Expected: list all errors, abort with summary message. [§Edge Cases]
- [ ] CHK065 Is the mixed-file-types case defined? — Directory contains .txt, .csv, .json files. Expected: only .json files processed. [§C-001]
- [ ] CHK066 Is the single-student edge case defined? — Only one JSON file. Expected: summary table, no histogram/cohort chart. [§C-003, §Edge Cases]
- [ ] CHK067 Is the all-same-cohort edge case defined? — Expected: single entry in cohort_summary, no cohort comparison chart. [§C-002, §C-003]
- [ ] CHK068 Is the all-errors-same-code edge case defined? — Every error is "R:DET". Expected: error_code_summary has 1 entry with 100%. [§C-002]
- [ ] CHK069 Is the zero-errors edge case defined? — Every student has error_rate = 0, errant_analysis.errors = []. Expected: error_code_summary empty, note in report. [§C-002]
- [ ] CHK070 Is the very-large-cohort edge case defined? — 50+ students. Expected: histogram generated (n≥10). [§C-003]
- [ ] CHK071 Is the title-max-length edge case defined? — Very long title (>200 chars). Expected: truncated or wrapped? [§data-model.md]
- [ ] CHK072 Is the path-with-special-characters edge case defined? — Path contains spaces, Unicode, or emoji. Expected: handled by Pathlib. [§C-001]
- [ ] CHK073 Is the draft-file-already-exists edge case defined? — outputs/drafts/<title>.md already exists. Expected: append timestamp suffix? [§data-model.md]
- [ ] CHK074 Is the chart-output-directory-fails edge case defined? — Cannot create charts/ subdirectory. Expected: FileNotFoundError with clear message. [§C-003]
- [ ] CHK075 Is the PDF-output-directory-unwritable edge case defined? — Output path on read-only filesystem. Expected: PermissionError caught, reported to user. [§C-004]
- [ ] CHK076 Is the multiple-insertion-points-same-index edge case defined? — Two custom sections both inserted after section 3. Expected: ask user to re-specify. [§Edge Cases, §data-model.md]
- [ ] CHK077 Is the insertion-after-last-section edge case defined? — Insert after section index 10 (References). Expected: valid if 0–10 range. [§data-model.md CustomSection]
- [ ] CHK078 Is the no-historical-data edge case defined? — No Supabase connection, no historical_data.json. Expected: empty trend data, trend chart skipped. [§C-002, §plan.md Component 2]
- [ ] CHK079 Is the grades-not-available (no error_rate) edge case defined? — All students have error_rate = None. Expected: "<40 words" note, no chart, table-only summary. [§data-model.md]
