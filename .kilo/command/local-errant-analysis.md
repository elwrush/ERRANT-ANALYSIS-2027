---
description: Run ERRANT grammatical error analysis on transcribed student essays
---
Load the `errant-analysis` skill from `.kilo/skills/errant-analysis/SKILL.md` and execute the full workflow:

1. Run `python src/errant_analysis.py` — the script will list available output files from `outputs/`
2. Select a file to analyze
3. The script corrects the essay text using Qwen3 8B via OpenRouter ($0.05/M input)
4. ERRANT compares original vs corrected and classifies errors by type
5. Output saved to `local-working/{folder}-{student_id}.json` with sentence pairs, error summary, markup, and error rate
