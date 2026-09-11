---
description: Rename ERRANT output JSONs to student_id.json, validated against Supabase classlist
agent: build
---

Load and follow the `rename-json-files` skill.

Run `python src/rename_json_files.py` and report renamed files plus any students not found in the classlist.

Arguments: $ARGUMENTS
