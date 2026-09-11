# Non-Functional Requirements Checklist — Report PDF Publishing

Checks whether performance, security, accessibility, and operational quality attributes are addressed.

- [ ] CHK164 No new package dependency. [§NFR-001]
- [ ] CHK165 Runtime delta from PNG compositing negligible (<~50ms/student). [§NFR-002]
- [ ] CHK166 Output remains A4 (595.28×841.89 pt). [§NFR-003]
- [ ] CHK167 Ghostscript no longer a prerequisite. [§NFR-004]
- [ ] CHK168 File size not materially larger after opaque re-encode. [§NFR-002]
- [ ] CHK169 No text/chart quality loss (charts stay vector). [§NFR-005]
- [ ] CHK170 Ruff clean / pytest parity. [§NFR-006]
- [ ] CHK171 No new subprocess/network calls. [§NFR-006]
