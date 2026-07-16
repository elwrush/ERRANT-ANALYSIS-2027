# Checklist: Edge Case Coverage

- [ ] CHK040 What happens to the config.py fallback if the `.env` file is missing and no environment variables are set? [Spec §Assumptions — not defined]
- [ ] CHK041 What happens to model validation if a pre-existing JSON file from the legacy pipeline is loaded (no `student_id` field, old schema)? [Spec — not defined]
- [ ] CHK042 Does the Playwright pipeline handle zero-page or single-page PDF generation (short text that doesn't fill one page)? [Plan §Phase 3, Tasks §T030]
- [ ] CHK043 Is there a defined behaviour for student essays with exactly 40 words (the boundary between error_rate=some and error_rate=None)? [Spec §Data Model §error_rate = None when <40 words]
- [ ] CHK044 Are filenames with special characters (Thai characters, spaces in class names) handled by the Jinja2→Playwright pipeline? [Spec — not defined]
- [ ] CHK045 What happens when `pixeldiff` reveals >1% difference — is there a defined re-tune threshold or automatic rejection? [Spec — not defined beyond "Tune CSS"]
- [ ] CHK046 What happens when `playwright install chromium` is run on a system without internet access? [Spec — not defined]
