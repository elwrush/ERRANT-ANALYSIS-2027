---
description: Sync student classlist data from docs/students.txt to Supabase
---

Load the `supabase-classlist` skill from `.kilo/skills/supabase-classlist/SKILL.md` and follow the workflow:

1. Ensure `SUPABASE_URL` and `SUPABASE_ESL_KEY` are set in environment
2. Run `python src/supabase_classlist.py`
3. The script deletes ALL existing records from `classlists`, then inserts fresh records from `docs/students.txt`
4. Reports counts of deleted, inserted, and errored rows
