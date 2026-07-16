# Requirement Completeness Checklist — Technical Report Writer

Checks whether all necessary requirements are documented across the feature spec.

- [ ] CHK001 Are requirements defined for ALL 11 baseline report sections? [§FR-004]
- [ ] CHK002 Is the interactive session flow fully specified (what questions asked, in what order, with what validation)? [§FR-001, FR-002, FR-003]
- [ ] CHK003 Is chart generation specified for all required chart types (ERRANT frequency, cohort comparison, error distribution, per-student trend)? [§FR-012]
- [ ] CHK004 Is the human review gate fully specified (pause, sign-off, revision request, cancel behaviour)? [§FR-010]
- [ ] CHK005 Are requirements defined for each Python helper subcommand (validate, aggregate, charts, render)? [§plan.md Component 2]
- [ ] CHK006 Is the Kilo CLI command `/write-technical-report` fully specified with all interaction steps? [§FR-001]
- [ ] CHK007 Are requirements defined for the Tavily rhetorical research step? [§FR-008]
- [ ] CHK008 Are requirements defined for citation format enforcement (APA 7th with page/para numbers)? [§FR-011, FR-014]
- [ ] CHK009 Are requirements defined for the authorial voice (Australian teacher, active voice, no Australianisms)? [§FR-009]
- [ ] CHK010 Are requirements defined for CEFR benchmarking against international standards? [§FR-004 Section 4]
- [ ] CHK011 Are requirements defined for error handling in every failure mode (missing data, invalid JSON, template missing, Playwright unavailable)? [§Edge Cases]
- [ ] CHK012 Are requirements defined for custom section insertion validation (index range, duplicate detection, max count)? [§FR-003, §data-model.md CustomSection]
