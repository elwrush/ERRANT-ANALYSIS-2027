# Checklist: Acceptance Criteria Quality

- [ ] CHK026 Is every success criterion in the spec objectively verifiable without subjective judgement? [Spec §Success Criteria]
- [ ] CHK027 Does the pixel-diff success criterion specify which tool (`pixelmatch`), threshold (<1%), and reference (saved Typst baseline)? [Spec §Success Criteria]
- [ ] CHK028 Is "Typst dependency removed" verified by `requirements.txt` only, or also by checking for `typst compile` subprocess calls in source? [Spec §Success Criteria, Plan §Phase 5]
- [ ] CHK029 Is the coverage target (60%) verifiable via a single `pytest --cov` command with a defined set of modules? [Spec §Success Criteria]
- [ ] CHK030 Is "no duplicated ERRANT code mappings" verifiable via a single `grep` command? [Spec §Success Criteria]
- [ ] CHK031 Is "all JSON writes use model_validate" verifiable via automated inspection (grep) rather than manual code review? [Spec §Success Criteria]
- [ ] CHK032 Are the acceptance criteria time-boxed? (e.g., "pipeline runs in < X seconds") [Spec — deliberately absent, but worth documenting]
