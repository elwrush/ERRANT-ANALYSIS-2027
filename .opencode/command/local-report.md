---
description: Generate student feedback PDF reports from ERRANT analysis via Jinja2 + Playwright, with alpha-free SVG charts and one standalone PDF per student
agent: build
---

Load and follow the `local-report` skill.

Ask which class folder to render (unless supplied below), then run `python src/generate_report.py "FOLDER_NAME"` and report the folder of standalone per-student PDFs.

Arguments / class folder: $ARGUMENTS
