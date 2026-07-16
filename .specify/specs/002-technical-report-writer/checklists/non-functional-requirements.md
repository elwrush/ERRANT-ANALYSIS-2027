# Non-Functional Requirements Checklist — Technical Report Writer

Checks whether performance, security, accessibility, and operational quality attributes are addressed.

- [ ] CHK080 Is PDF generation performance specified? — NFR-001: 120s for full report with charts. [§NFR-001]
- [ ] CHK081 Is Python-to-PDF render time bounded? — NFR-001 covers the full pipeline; confirm measurement includes chart generation + template rendering + Playwright PDF.
- [ ] CHK082 Is Playwright memory usage bounded? — NFR-002: 500 MB RSS during `html_to_pdf()`. [§NFR-002]
- [ ] CHK083 Is Markdown draft generation latency specified? — NFR-003: 30s from user confirmation. [§NFR-003]
- [ ] CHK084 Is A4 printability ensured? — NFR-004: page size 595.28 × 841.89 pts with 0.75in (1.6cm) margins. [§NFR-004]
- [ ] CHK085 Is grayscale-printing accessibility specified? — FR-007 (grayscale patterns) is a rendering constraint, not a performance one. Confirm coverage in NFRs.
- [ ] CHK086 Is concurrency specified? — How many concurrent reports can be generated? Single-session sequential assumed.
- [ ] CHK087 Is input validation security specified? — Validated via Pydantic; no path traversal or injection vectors identified. Confirm no `os.system()` or `subprocess` in the Python helper.
- [ ] CHK088 Is API key security specified? — Tavily key accessed via environment variable (Kilo's builtin skill). No key logged or exposed.
- [ ] CHK089 Is PDF file size bounded? — No max PDF file size specified. Should be <10 MB for typical cohort report.
- [ ] CHK090 Is disk space for chart images bounded? — No cleanup requirement specified. Charts accumulate in `<output_dir>/charts/`.
- [ ] CHK091 Is the report file naming collision-free? — Title sanitisation prevents name collisions? Only if title is unique. [§Edge Cases, §data-model.md]
- [ ] CHK092 Is the system font-dependent? — Template uses Roboto system font. Falls back to sans-serif. [§research.md]
- [ ] CHK093 Is there a WSL/Windows compatibility requirement? — Project runs on WSL (Linux). Confirm Playwright works in WSL headless mode.
