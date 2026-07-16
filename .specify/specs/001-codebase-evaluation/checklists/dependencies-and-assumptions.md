# Checklist: Dependencies & Assumptions

- [ ] CHK055 Is the assumption that "errant/spaCy playwell with Python 3.14" verified by checking PyPI wheel availability before proceeding? [Spec §Assumptions #1, §Research]
- [ ] CHK056 Is the assumption that all 6 one-shot scripts are safe to archive verified by git log or last-execution-date? [Spec §Assumptions #3]
- [ ] CHK057 Are the external runtime dependencies of the Playwright pipeline documented (system libraries required by Chromium)? [Research — `playwright install chromium --with-deps` handles this; is it documented?]
- [ ] CHK058 Is the dependency on `pydeps` for FR-001 declared in requirements.txt, or assumed to be installed separately? [Spec §FR-001 — tool not named in requirements]
- [ ] CHK059 Is there a documented assumption about network latency for the 3 LLM API calls (correction, summary, ingestion)? [Spec — absent]
- [ ] CHK060 Is the dependency between `config.py` and all consuming modules explicitly documented (import graph)? [Plan §Architecture, §Dependency Graph]
- [ ] CHK061 Is there a documented assumption about the existing `pypdf` or `pdftk` fallback being removed? [Spec §FR-002 — yes, removed]
