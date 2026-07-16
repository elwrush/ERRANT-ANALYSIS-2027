# Checklist: Scenario Coverage

- [ ] CHK033 Is there a defined flow for how an operator triggers the refactored report generation? [Spec, Plan — operator interaction is implicit]
- [ ] CHK034 Is there a defined flow for falling back from Playwright to an alternative if Chromium cannot launch on the target machine? [Spec §Edge Cases — graceful error but no fallback]
- [ ] CHK035 Is the migration path for existing `.typ` files in `outputs/` defined (archive, skip, or convert)? [Spec §Edge Cases]
- [ ] CHK036 Is there a defined scenario for running the pipeline with Supabase unavailable? [Spec §Edge Cases — graceful skip defined]
- [ ] CHK037 Is the scenario for the `--engine typst` backwards-compatibility flag (dual codepath during transition) defined? [Plan §Quickstart §Rollback — mentioned but not in spec]
- [ ] CHK038 Is the interleaving of Phase 4 (response_format) and Phase 6 (PDF) safe if both modify `generate_report.py` imports? [Tasks §Dependency Graph — sequential ordering addresses this]
- [ ] CHK039 Is there a defined rollback scenario if the Playwright PDF output is rejected during review? [Plan §Quickstart §Rollback Plan]
