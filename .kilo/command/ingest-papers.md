---
description: Ingest and transcribe handwritten student essays from images using Gemini via OpenRouter
---
Load the `ingest-images` skill from `.kilo/skills/ingest-images/SKILL.md` and follow the workflow:

1. Ensure `OPENROUTER_API_KEY` is set in `.env` or environment
2. Run `python src/ingest.py`
3. The script will enumerate subfolders in `inputs/` — select one
4. Specify how many image pages per essay (affects grouping)
5. The script processes each student's pages serially with jitter, saves JSON output to `outputs/{folder}/{student_id}.json`
