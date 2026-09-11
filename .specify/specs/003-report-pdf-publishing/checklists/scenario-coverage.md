# Scenario Coverage Checklist — Report PDF Publishing

Checks whether all user flows and system scenarios are addressed in the requirements.

- [ ] CHK155 Happy path: `python src/generate_report.py "M2-3B"` → N standalone PDFs. [§FR-004]
- [ ] CHK156 Single-student folder → one PDF, no merge. [§FR-004]
- [ ] CHK157 `technical_report_writer.py render` → single PDF, no gs. [§FR-001]
- [ ] CHK158 Re-run same day → timestamped filenames don't clash. [§FR-006]
- [ ] CHK159 Acrobat open/print → no flattening prompt. [§Success Criteria]
- [ ] CHK160 Developer without Ghostscript → pipeline succeeds. [§FR-001]
- [ ] CHK161 Grayscale print of per-student PDF → chart legible. [§FR-003]
- [ ] CHK162 Test suite runs without gs. [§FR-009]
- [ ] CHK163 Legacy outputs unaffected. [§Edge Cases]
