# Edge Case Coverage Checklist — Report PDF Publishing

Checks whether boundary conditions and unusual inputs are defined in the requirements.

- [ ] CHK145 Image already RGB → re-encode opaque PNG (visual no-op). [§Edge Cases]
- [ ] CHK146 Palette PNG with `transparency` index → composite over white. [§Edge Cases]
- [ ] CHK147 LA (grayscale + alpha) → composite → RGB. [§Edge Cases]
- [ ] CHK148 Missing logo file → existing fallback (`""` in tech writer; path error in generate_report). [§Edge Cases]
- [ ] CHK149 Image larger than page → CSS sizing unchanged. [§Edge Cases]
- [ ] CHK150 Zero students → existing error exit. [§Edge Cases]
- [ ] CHK151 word_count<40 / error_rate None → chart still rendered; no change. [§Edge Cases]
- [ ] CHK152 `m2_3b_report.html` / `report.html` already opacity-free → no change. [§Edge Cases]
- [ ] CHK153 gs not installed → no fallback branch remains. [§Edge Cases]
- [ ] CHK154 Legacy merged PDFs in `PDF/` → untouched by a new run. [§Edge Cases]
