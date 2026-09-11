# Dependencies & Assumptions Checklist — Report PDF Publishing

Checks whether all external dependencies and implicit assumptions are documented and validated.

- [ ] CHK172 Pillow ≥10 available. [§Assumptions #1]
- [ ] CHK173 Chromium emits no transparency groups for opaque content — verified in T019. [§Assumptions #2]
- [ ] CHK174 `tech_report.html` is hard-coded; opacity-only change is safe. [§Assumptions #3]
- [ ] CHK175 Pre-blended colours preserve appearance. [§Assumptions #4]
- [ ] CHK176 Removing padding changes page counts (accepted). [§Assumptions #5]
- [ ] CHK177 PyMuPDF stays for annotations; `generate_report` no longer needs it. [§Assumptions #6]
- [ ] CHK178 `m2_3b_report.html` remains the section-driven single-class path. [§Assumptions #7]
- [ ] CHK179 Existing 5 known test failures; this change fixes 1. [§Success Criteria]
