# Acceptance Criteria Quality Checklist — Technical Report Writer

Checks whether success criteria are measurable, objective, and verifiable.

- [ ] CHK034 Is "report compiles without errors" objectively measurable? — `python src/generate_report.py` exit code 0 and non-empty PDF. Yes — PASS.
- [ ] CHK035 Is "all 11 baseline sections present" objectively measurable? — Text extraction from PDF can verify section headings. Specify expected headings exactly.
- [ ] CHK036 Is "charts use grayscale-safe patterns" objectively verifiable? — "Visual inspection" is subjective. Specify a pixel-level check (RGB channels equal in non-text areas) or explicit hatch pattern verification.
- [ ] CHK037 Is "first draft in Markdown" objectively verifiable? — `.md` file in outputs/ before any `.pdf`. Yes — PASS.
- [ ] CHK038 Is "human review gate enforced" objectively verifiable? — Pipeline pause without automated continuation. Define: does the agent block until user types "proceed"?
- [ ] CHK039 Is "all references include page numbers" verifiable via grep? — Pattern `(p\. \d+)` or `(para\. \d+)` in Markdown draft. Yes — PASS.
- [ ] CHK040 Is "Tavily search invoked" verifiable? — Logs confirm skill call. Define expected log format.
- [ ] CHK041 Is "Pydantic validation on data load" verifiable? — `model_validate()` call on input JSONs. Grep for `model_validate` in the code path. Yes — PASS.
- [ ] CHK042 Is "no Typst/Pandoc dependency" verifiable? — Grep for `typst`, `pandoc`, `pypdf` in requirements.txt. Yes — PASS.
- [ ] CHK043 Is NFR-001 (120s report generation) measured correctly? — `time python src/generate_report.py` needs a specific test data size to produce comparable results.
- [ ] CHK044 Is NFR-002 (500 MB RSS) measured correctly? — `psutil` measurement during `html_to_pdf()`. Define measurement point and duration.
- [ ] CHK045 Is NFR-003 (30s draft generation) ambiguous? — "User confirming data location and title" needs precise timing start point (after last confirmation input).
- [ ] CHK046 Is NFR-004 (A4 paper size) verifiable? — PyMuPDF page size check `595.28 × 841.89 pts`. Yes — PASS.
