# Checklist: Non-Functional Requirements

- [ ] CHK047 Are PDF generation performance requirements defined? (e.g., "must generate 1 student PDF in < 5 seconds") [Spec — absent]
- [ ] CHK048 Are font rendering requirements defined? (e.g., must match Typst output which uses Roboto from TinyTeX) [Spec §FR-002, Plan §Phase 3 — pixel-equivalent implies font fidelity]
- [ ] CHK049 Are batch processing throughput requirements defined? (e.g., "batch of 36 students must complete in < 1 hour") [Spec — absent]
- [ ] CHK050 Are security requirements for API key handling defined? (current `.env` pattern is adequate; is explicit documentation needed?) [Spec — not addressed]
- [ ] CHK051 Are file size limits for PDF output defined? (e.g., each student PDF must be < 2 MB) [Spec — absent]
- [ ] CHK052 Is there an accessibility requirement for the PDF output? (e.g., tagged PDF for screen readers) [Spec — absent, low priority]
- [ ] CHK053 Is Python 3.14 compatibility enforced via CI or only documented as a target? [Spec §Clarifications Q3, Plan §Tech Stack]
- [ ] CHK054 Is there a stated assumption about the disk space required for Playwright's bundled Chromium (~200-400 MB)? [Spec — absent]
