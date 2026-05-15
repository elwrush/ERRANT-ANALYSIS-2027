---
description: Rename ERRANT output JSONs to student_id.json, validated against Supabase classlist
---

Load the `rename-json-files` skill from `.kilo/skills/rename-json-files/SKILL.md` and execute the workflow:

1. Ensure ERRANT analysis is complete and files exist in `local-working/`
2. Run `python src/rename_json_files.py`
3. The script loops through all JSONs in `local-working/`, extracts `student_id`, validates against Supabase classlist
4. Valid files are renamed to `{student_id}.json`
5. Invalid files are flagged for manual rename
