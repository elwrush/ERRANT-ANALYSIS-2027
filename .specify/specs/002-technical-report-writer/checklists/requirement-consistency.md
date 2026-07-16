# Requirement Consistency Checklist — Technical Report Writer

Checks whether requirements align without contradictions or conflicts.

- [ ] CHK025 Does FR-005 (Jinja2→Playwright pipeline) conflict with FR-010 (Markdown first draft)? — They are sequential: FR-010 describes the draft step BEFORE PDF rendering in FR-005. Confirm ordering is explicit.
- [ ] CHK026 Does FR-008 (Tavily research before prose) conflict with FR-009 (Australian voice)? — Tavily rules should complement, not override, the voice requirement. Confirm precedence rules for conflicting style guidance.
- [ ] CHK027 Are FR-007 (grayscale-safe charts) and FR-012 (charts for ERRANT codes, cohort, frequency) consistent? — Grayscale must apply to all three chart types.
- [ ] CHK028 Does FR-003 (custom sections with rhetorical questions) conflict with FR-004 (11 baseline sections)? — Confirm that custom sections are additional, not replacements.
- [ ] CHK029 Does NFR-001 (120s PDF generation) conflict with NFR-003 (30s draft generation)? — Different pipeline steps, but confirm the combined path is within user tolerance.
- [ ] CHK030 Is FR-006 (header from WRITING_ASSESSMENT_NEW) compatible with the standalone Jinja2→Playwright pipeline? — Header is a Jinja2 HTML/CSS template; confirm it can be included/extended without modification.
- [ ] CHK031 Do FR-011 (page/para numbers for sources) and FR-014 (APA 7th) align? — APA 7th requires page numbers for direct quotations; confirm the spec expects them for ALL references, not just quotes.
- [ ] CHK032 Does the Tavily research step (FR-008) use Tavily as a Kilo skill (agent-resolved) or as a Python library call? — Spec says Kilo skill. Confirm no Python-level Tavily dependency is introduced.
- [ ] CHK033 Are the three [NEEDS CLARIFICATION] markers in Assumptions resolved in the Clarifications table? — Check assumptions 3 and 4 have matching clarifications.
