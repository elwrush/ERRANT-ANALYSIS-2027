---
description: Run ERRANT grammatical error analysis on transcribed student essays
---
Load the `errant-analysis` skill from `.kilo/skills/errant-analysis/SKILL.md` and execute the full workflow:

1. Run `python src/add_word_count.py` — counts words in `student_text` and writes `word_count` key to each JSON
2. Run `python src/errant_analysis.py` — the script will list available output files from `outputs/`
3. Select a file to analyze
4. The script corrects the essay text using Mistral Small 3.2 24B via OpenRouter
5. ERRANT compares original vs corrected and classifies errors by type
6. Output saved to `local-working/{folder}-{student_id}.json` with sentence pairs, error summary, markup, and error rate
