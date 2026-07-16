# Dependencies & Assumptions Checklist — Technical Report Writer

Checks whether all external dependencies and implicit assumptions are documented and validated.

- [ ] CHK094 Is the Tavily API availability assumption documented? — Confirmed in Clarifications #4: Tavily is configured. [§Assumptions #3, §Clarifications #4]
- [ ] CHK095 Is the WRITING_ASSESSMENT_NEW header format assumption documented? — Confirmed in Clarifications #1: it is a Jinja2 HTML/CSS template. [§Assumptions #2, §Clarifications #1]
- [ ] CHK096 Is the ErrantOutput schema assumption documented? — Assumption #1: JSONs follow ErrantOutput schema. Medium confidence — needs schema check before first run. [§Assumptions #1]
- [ ] CHK097 Is the Chromium/Playwright installation assumption documented? — Listed as a runtime dependency. Confirm `playwright install chromium` in setup instructions. [§quickstart.md]
- [ ] CHK098 Is the Python version dependency documented? — Python 3.14 as per project constitution. [§research.md, §CONSTITUTION]
- [ ] CHK099 Is the Matplotlib Agg backend dependency documented? — Required for headless chart generation on WSL. [§research.md]
- [ ] CHK100 Are the logo file assumptions documented? — Images/ACT.png and images/cambridge.png must exist. Pre-copied during Phase 1 (T002). [§plan.md Setup]
- [ ] CHK101 Is the Roboto font assumption documented? — Reports assume Roboto system font for consistent rendering. Fallback to sans-serif specified. [§research.md]
- [ ] CHK102 Is the Supabase connectivity assumption documented? — Historical data fetch uses Supabase; falls back to local JSON file. Graceful degradation documented. [§C-002, §plan.md Component 2]
- [ ] CHK103 Is the "no Pandoc/Typst" constraint documented? — Yes, in CONSTITUTION Article 5.2. Confirmed no dependency in requirements.txt. [§Success Criteria]
- [ ] CHK104 Is the WSL environment assumption documented? — Project runs in WSL/Linux. All paths use forward slashes. [§CONSTITUTION]
- [ ] CHK105 Is the Ghostscript dependency documented? — Mentioned as optional in plan.md. Confirm whether it is required for the technical report PDF pipeline. [§plan.md Component 2]
- [ ] CHK106 Is the Jinja2 FileSystemLoader path assumption documented? — Template path resolved relative to project root. Confirm in scripts that `sys.path` is set correctly. [§C-004, §plan.md]
