---
description: Run ERRANT grammatical error analysis on transcribed student essays
---
Load the `errant-analysis` skill from `.kilo/skills/errant-analysis/SKILL.md` and execute the full workflow:

1. For research batch mode: run `python src/research_prep.py` — fetches sampled records from Supabase, cleans HTML, filters ≥40 words, writes one JSON per record to `outputs/research/{record_id}.json`
2. For batch processing: `python src/errant_analysis.py --batch research` — processes all files in `outputs/research/` with 5 parallel workers
3. For interactive mode: `python src/errant_analysis.py` — lists available output files from `outputs/`
4. The script corrects the essay text using `gpt-4o-mini` via OpenAI direct API (2 correction passes at temps 0.1, 0.5 with edit-level majority voting — both must agree — + summary)
5. ERRANT compares original vs corrected and classifies errors by type
6. Output saved to `local-working/{folder}-{record_id}.json` with sentence pairs, error summary, markup, and error rate
