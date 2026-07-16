# Cross-Artifact Analysis — Technical Report Writer

## Legend

| Severity | Meaning |
|----------|---------|
| 🔴 CRITICAL | Constitution violation, zero-coverage blocking baseline |
| 🟠 HIGH | Duplicate/conflicting requirement, untestable criterion, missing task |
| 🟡 MEDIUM | Terminology drift, missing non-functional coverage |
| 🔵 LOW | Style, redundancy, minor inaccuracy |

---

## 🔴 CRITICAL Findings

### F001: Ghostscript mandatory in constitution, optional in plan
**Constitution Article 5.1**: `Jinja2 templates → Playwright PDF → **Ghostscript flatten**`
**Plan §Component 2**: `Optional: Ghostscript flatten`
**Conflict**: The constitution mandates Ghostscript in the pipeline; the plan treats it as optional. One must yield.
**Location**: `CONSTITUTION.md:68` vs `plan.md:102`

### F002: Tavily listed as Python dependency in plan, but spec says Kilo skill
**Plan §Dependencies table**: `tavily | Kilo skill | Rhetorical research` — The column says "Source" is `requirements.txt` for other entries but `tavily` is marked as "Kilo skill". However the table groups all entries under "Dependency | Source | Purpose" without distinguishing pip vs skill. This could cause confusion: a developer may try `pip install tavily` but no such Python package is required.
**FR-008**: `via Kilo's builtin capability`
**Location**: `plan.md:161`

---

## 🟠 HIGH Findings

### F003: Missing task for FR-014 (APA 7th references)
**FR-014**: References section MUST be formatted in APA 7th edition style.
**Tasks coverage**: No task explicitly handles APA formatting. T023 (Markdown draft) and T026 (citation enforcement) partially cover it but neither mentions APA 7th. APA style has specific formatting rules (hanging indent, author formatting, DOI format) that are not addressed.
**Location**: `spec.md:42` — no matching task in `tasks.md`

### F004: Success criterion references wrong file path
**Spec §Success Criteria**: `python src/generate_report.py` exits 0
**Plan §Project Structure**: New file is `src/technical_report_writer.py` (separate from existing `src/generate_report.py`)
**Problem**: The success criterion points to the old file, not the new one. A developer verifying against this criterion would run the wrong script.
**Location**: `spec.md:50`

### F005: Margin mismatch between spec and contract
**Spec NFR-004**: `0.75in margins`
**Contract C-004 CSS**: `margin: 1.6cm` (≈0.63in)
**WRITING_ASSESSMENT_NEW template**: `margin: 1.6cm`
**Problem**: Spec says 0.75in but contract and source template use 1.6cm. These differ by ~2mm. Minor visually but the spec must match the implementation target.
**Location**: `spec.md:85` vs `contracts/C-004-pdf-rendering.md:63`

### F006: FR-006 task doesn't reference WRITING_ASSESSMENT_NEW template extension
**FR-006**: Report MUST use document header from `C:\PROJECTS\WRITING_ASSESSMENT_NEW`.
**T014**: Create `templates/tech_report.html` — describes building a new masthead from scratch.
**Problem**: FR-006 says to USE the existing header, but T014 builds a fresh one. If the intent is to extend/include the WRITING_ASSESSMENT_NEW template, T014 should say `{% extends %}` or `{% include %}` with the path. If the intent is to build a compatible duplicate, T014 should say "replicate the C·E·L Mathayom masthead matching WRITING_ASSESSMENT_NEW's template".
**Location**: `spec.md:34` vs `tasks.md:38`

---

## 🟡 MEDIUM Findings

### F007: US2 + US3 not independently testable
**US2** (P1): Charts illustrating error patterns
**US3** (P1): Grayscale-safe patterns
**Both covered by**: T007/T008
**Problem**: US2 requires charts exist; US3 requires those same charts to be grayscale-safe. They share the same implementation and same tests, so either can fail independently but the tasks don't distinguish them. No task explicitly verifies "charts exist" separately from "charts are grayscale."
**Location**: `tasks.md:22-23`

### F008: No objective test criterion for "Australian teacher voice"
**FR-009**: Authorial voice of an educated Australian teacher.
**Success criteria**: Not listed in spec success criteria table. No grep-able pattern. "Australian teacher voice" is subjective.
**T019**: "Implement agent prose composition with Australian teacher voice style rules" — but no test validates this output characteristic.
**Location**: `spec.md:37`

### F009: FR-002 question order not specified
**FR-002**: Interactive session asks for data path, title, additional sections.
**Problem**: Order is not specified. Should data path be asked first (so title can default to folder name), or title first? The plan shows a specific order; the spec doesn't mandate one. If code implements a different order than the plan, it technically still meets FR-002.
**Location**: `spec.md:30`

### F010: "Tavilly" typo
**plan.md:76**: `Tavilly research` should be `Tavily research`.
**Location**: `plan.md:76`

### F011: Success criterion "human review gate enforced" is vague
**Spec**: `Pipeline pauses after .md generation, waits for user confirmation`
**Problem**: "Waits for user confirmation" is not precise enough for automated verification. Does the agent loop with `input()`? Does it present a yes/no question? What counts as confirmation? The existing edge case says "User cancels → save draft with note" but doesn't define what "confirmation" looks like.
**Location**: `spec.md:55`

---

## 🔵 LOW Findings

### F012: Duplicate "visual inspection" in success criteria
**Spec**: "Visual inspection of PDF confirms no color-only differentiation" appears as a success criterion.
**Checklist CHK036** flagged this as subjective. No automated test validates grayscale compliance.
**Location**: `spec.md:53`

### F013: Plan dependence table uses `tavily` as a pip-style entry
**Plan**: Dependencies table lists `tavily` alongside `jinja2`, `playwright`, etc. but Tavily is a Kilo skill, not a pip package. The table's "Source" column says "Kilo skill" for tavily but "requirements.txt" for everything else — inconsistent presentation.
**Location**: `plan.md:161`

### F014: No task for output directory creation in render path
**C-004**: `render_technical_report()` takes an `output_path`.
**Edge case**: Directory containing the output path may not exist. No task ensures the Python helper creates parent directories on render.
**Location**: `tasks.md:28`

---

## Coverage Summary

| FR-ID | Tasks covering it | Status |
|-------|-------------------|--------|
| FR-001 | T013, T015, T016 | ✅ Covered |
| FR-002 | T013, T015, T016 | ✅ Covered |
| FR-003 | T020, T021 | ✅ Covered |
| FR-004 | T014, T023 | ✅ Covered |
| FR-005 | T009, T010, T014, T015 | ✅ Covered |
| FR-006 | T002, T014 | ⚠️ T014 builds new template, doesn't extend existing one (F006) |
| FR-007 | T007, T008 | ✅ Covered |
| FR-008 | T017, T018, T027 | ✅ Covered |
| FR-009 | T019 | ⚠️ No objective test criterion (F008) |
| FR-010 | T009, T010, T022, T023, T024 | ✅ Covered |
| FR-011 | T025, T026 | ✅ Covered |
| FR-012 | T007, T008 | ✅ Covered |
| FR-013 | T003, T004 | ✅ Covered |
| FR-014 | (none explicit) | ❌ **No dedicated task** (F003) |

| US | Phase covering it | Status |
|----|-------------------|--------|
| US1 (P1) | Phase 3 | ✅ |
| US2 (P1) | Phase 2 (charts) | ⚠️ Not independently testable from US3 (F007) |
| US3 (P1) | Phase 2 (charts) | ⚠️ Not independently testable from US2 (F007) |
| US4 (P1) | Phase 4 | ⚠️ No objective voice test (F008) |
| US5 (P2) | Phase 5 | ✅ |
| US6 (P2) | Phase 5 | ✅ |
| US7 (P2) | Phase 6 | ✅ |
| US8 (P3) | Phase 7 | ✅ |
| US9 (P3) | Phase 7 | ✅ |

---

## Remediation Suggestions

Before proceeding to `/speckit.implement`, the following resolutions are recommended:

| Finding | Suggested Fix | Difficulty |
|---------|--------------|------------|
| F001 | Either make Ghostscript mandatory in plan.md:102 OR amend Constitution 5.5 to allow optional Ghostscript for the technical report pipeline. | Low |
| F002 | Remove `tavily` from the Dependencies table in plan.md; add a note that Tavily is a Kilo skill, not a pip package. | Low |
| F003 | Add task T033: "Implement APA 7th references section formatting" in Phase 6 (or bundle into T026 with explicit APA rules). | Low |
| F004 | Update success criterion path from `src/generate_report.py` to `src/technical_report_writer.py`. | Low |
| F005 | Align NFR-004 margin to 1.6cm (matching WRITING_ASSESSMENT_NEW and C-004). | Low |
| F006 | Update T014 to reference `{% extends %}` or `{% include %}` from the WRITING_ASSESSMENT_NEW template path. | Low |
| F007 | Add a single-line test assertion that confirms chart files are created (separate from the grayscale check). | Low |
| F008 | Add a success criterion with an automated text-analysis check or an approved sample paragraph. | Medium |
| F009 | Specify the question order in FR-002 (recommend: data path → title → custom sections). | Low |
| F010 | Fix typo "Tavilly" → "Tavily" in plan.md:76. | Low |
| F011 | Define "user confirmation" precisely (e.g., user types "proceed" or "generate"). | Low |
| F014 | Add `output_path.parent.mkdir(parents=True, exist_ok=True)` to C-004 implementation. | Low |
