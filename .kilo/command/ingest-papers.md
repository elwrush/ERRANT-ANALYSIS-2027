---
description: Ingest and transcribe handwritten student essays from images using Gemini via OpenRouter
---
Load the `ingest-images` skill from `.kilo/skills/ingest-images/SKILL.md` and follow the workflow:

1. Ensure `OPENROUTER_API_KEY` is set in `.env` or environment
2. Run `python src/ingest.py`
3. The script enumerates subfolders in `inputs/` with a numbered list — the user types the number to select one
4. The script then asks for pages per essay — the user types a numeral (e.g. `1`, `2`, `3`, `4`)
5. The script processes each student's pages serially with jitter, saves JSON output to `outputs/{folder}/{student_id}.json`
