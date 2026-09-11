# Acceptance Criteria Quality Checklist — Report PDF Publishing

Checks whether success criteria are measurable, objective, and verifiable.

- [ ] CHK135 Is "no Ghostscript" measurable? — `grep -rn "pdfwrite\|gs " src/` returns no report-pipeline hits. PASS.
- [ ] CHK136 Is "all embedded images opaque" measurable? — decode data URIs; PIL mode == RGB. PASS.
- [ ] CHK137 Is "alpha-free charts" measurable? — SVG text has no opacity attributes. PASS.
- [ ] CHK138 Is "single files only" measurable? — N students → N PDFs; no `*-errant-report.pdf`. PASS.
- [ ] CHK139 Is "no flattening prompt in Acrobat" measurable? — no `/SMask` and no transparent `/Group`. PASS (proxy).
- [ ] CHK140 Is "naming unchanged" measurable? — filename regex. PASS.
- [ ] CHK141 Is "docs updated" measurable? — grep SKILL/command/AGENTS for "interleaved"/"Ghostscript". PASS.
- [ ] CHK142 Is the `test_charts_grayscale` fix measurable? — green in `pytest`. PASS.
- [ ] CHK143 Is NFR "no new dependency" measurable? — `requirements.txt` unchanged. PASS.
- [ ] CHK144 Is NFR "no gs prerequisite" measurable? — run with gs absent. PASS.
