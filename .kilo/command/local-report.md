---
description: Generate Typst report booklets from ERRANT analysis with summary, error charts, and PDF output
---

Load the `local-report` skill from `.kilo/skills/local-report/SKILL.md` and execute the workflow:

1. Ensure `OPENROUTER_API_KEY`, `SUPABASE_URL`, and `SUPABASE_ESL_KEY` are set
2. Run `python src/generate_report.py [folder_name]` — processes all ERRANT outputs in `local-working/`
3. For each student, the script:
   a. Queries historical error data from Supabase `error_reports` table
   b. Generates a line chart (matplotlib) showing error rate over time
   c. Builds a 4-page Typst booklet with summary, writing samples, error details
   d. Compiles the Typst file to PDF in `PDF/{folder}/{dd-mm-yy}-{class}-{student_id}.pdf`
4. Reports counts of generated PDFs and any compilation errors
