# Checklist: Requirement Clarity

- [ ] CHK012 Is "pixel-equivalent" (FR-002) precisely defined — same-student, same-page-count, same-rendering-engine comparison? [Spec §FR-002, §Success Criteria]
- [ ] CHK013 Is the <1% pixel-diff threshold explicitly stated as a requirement or as an aspirational target? [Spec §Success Criteria]
- [ ] CHK014 Does "all shared constants" (FR-003) include a definitive list of what belongs in `config.py` vs what stays inline? [Spec §FR-003, §Data Model §ConfigModel]
- [ ] CHK015 Is the "one canonical location" for ERRANT_CODE_TO_COLUMN (FR-004) named (which file)? [Spec §FR-004]
- [ ] CHK016 Does FR-005 clarify whether `response_format` is enforced at the client level (single wrapper) or per-call-site? [Spec §FR-005, §Plan §Tech Stack]
- [ ] CHK017 Is "meaningful unit tests" (FR-007) operationalised — what distinguishes meaningful from trivial tests? [Spec §FR-007]
- [ ] CHK018 Are the terms "module" vs "script" vs "source file" used consistently throughout the spec? [Spec — mixed usage of "scripts", "modules", "files"]
- [ ] CHK019 Is "last-use date" (FR-008) defined — last git commit, last manual execution, or last Supabase query reference? [Spec §FR-008]
