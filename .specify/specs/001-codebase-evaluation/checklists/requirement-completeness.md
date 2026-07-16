# Checklist: Requirement Completeness

- [ ] CHK001 Are all 8 user stories (US-P1-1 through US-P3-2) fully addressed by at least one functional requirement? [Spec §User Stories, §Functional Requirements]
- [ ] CHK002 Does every functional requirement (FR-001 through FR-008) trace to at least one user story? [Spec §Functional Requirements, §User Stories]
- [ ] CHK003 Are the 6 one-shot scripts listed in FR-008 exactly the same 6 that appear in US-P3-2's description? [Spec §FR-008, §US-P3-2]
- [ ] CHK004 Does the dependency graph requirement (FR-001) specify which tool to use and what output format is expected? [Spec §FR-001]
- [ ] CHK005 Does the PDF pipeline requirement (FR-002) define what "equivalent output" means (pixel-diff threshold)? [Spec §FR-002, §Clarifications Q1]
- [ ] CHK006 Is the scope of `response_format` enforcement (FR-005) explicit about which API calls it covers (correction, summary, ingestion)? [Spec §FR-005, §Research]
- [ ] CHK007 Does FR-006 specify whether model validation applies only to new writes, or also to reads of existing JSONs? [Spec §FR-006]
- [ ] CHK008 Are the 3 core modules requiring >60% coverage (FR-007) explicitly named? [Spec §FR-007]
- [ ] CHK009 Is there a requirement for what happens when Playwright/Chromium is not installed at runtime? [Spec §Edge Cases]
- [ ] CHK010 Is there a requirement for backward compatibility with existing Errput files generated before refactoring? [Spec §Edge Cases]
- [ ] CHK011 Are the non-functional attributes (performance, security, accessibility) covered for the Playwright PDF pipeline? [Spec §Non-Functional — currently absent]
