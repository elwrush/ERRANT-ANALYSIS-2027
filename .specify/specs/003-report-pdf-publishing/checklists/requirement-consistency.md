# Requirement Consistency Checklist — Report PDF Publishing

Checks whether requirements align without contradictions or conflicts.

- [ ] CHK127 Does FR-001 conflict with spec 002 `plan.md:110` (gs flatten)? — 003 supersedes; recorded.
- [ ] CHK128 Does FR-003 conflict with keeping the SVG format? — No; vector + opaque is consistent.
- [ ] CHK129 Does FR-004 conflict with SKILL.md "Interleaved merge (always)"? — FR-008 must update it.
- [ ] CHK130 Does FR-004 conflict with the 4-page padding rationale? — Padding existed for collation; removing both is consistent.
- [ ] CHK131 Does FR-005 conflict with the old delete-after-merge step? — It explicitly reverses it.
- [ ] CHK132 Does FR-002 conflict with visual identity? — No; white background matches the page.
- [ ] CHK133 Does FR-006 conflict with removing the merged `-errant-report.pdf`? — Different artifacts; individual naming unchanged.
- [ ] CHK134 Does FR-009 conflict with the AGENTS.md known-failing-test baseline? — It reduces failures; baseline note updates.
