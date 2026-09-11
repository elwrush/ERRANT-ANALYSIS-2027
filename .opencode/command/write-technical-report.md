---
description: Generate a technical assessment report — ERRANT data → validate → aggregate → charts → Markdown draft → human sign-off → PDF
agent: build
---

Run the interactive `write-technical-report` workflow end to end:

1. Ask the user for: path to the data directory, report title, and whether additional sections are needed.
2. If additional sections: list the 11 baseline sections and prompt for a rhetorical question + insertion point per custom section.
3. Run a Tavily search for rhetorical best practices and compile the results into inline style rules.
4. `python src/technical_report_writer.py validate <path>` — check the input JSONs.
5. `python src/technical_report_writer.py aggregate <path>` — aggregated statistics.
6. `python src/technical_report_writer.py charts <path> <output_dir>` — grayscale-safe charts.
7. Compose the Markdown draft with all sections, inline citations with page/para numbers, and APA 7th references as a JSON code fence.
8. Annotate each cited source PDF via PyMuPDF (yellow highlight + sticky note with the report section) into `references/annotated/`.
9. Generate `references/citation-map.md` mapping citations to source files and pages.
10. Write the draft to `outputs/drafts/<title-slug>.md`.
11. Present the draft + citation map + annotated PDFs to the user for review.
12. Wait for explicit sign-off ("proceed", "generate", "sign off") or cancellation.
13. On sign-off: `python src/technical_report_writer.py render <draft> <output.pdf>`.
14. On cancel: save the draft with a "DRAFT — not signed off" suffix.

Dependencies: `src/technical_report_writer.py`, `templates/tech_report.html`, `images/ACT.png`, `images/cambridge.png`, `outputs/drafts/`, `references/annotated/`.

Arguments / data path: $ARGUMENTS
