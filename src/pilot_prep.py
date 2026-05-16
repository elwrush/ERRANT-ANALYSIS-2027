#!/usr/bin/env python3
"""Fetch student 29579 records, clean HTML, write temp JSON for ERRANT."""
import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ESL_KEY"])

r = c.table("student_submissions").select("*").eq("student_id", "29579").ilike("skill", "Writing").order("submission_date").execute()
records = r.data

print(f"Found {len(records)} records for student 29579")

texts = []
total_wc = 0
for rec in records:
    txt = rec.get("student_text") or ""
    wc = rec.get("word_count") or 0
    total_wc += wc
    # Clean HTML: <br> → newline, strip any remaining tags
    txt = re.sub(r"<br\s*/?>", "\n", txt, flags=re.IGNORECASE)
    txt = re.sub(r"<[^>]+>", "", txt)
    texts.append(txt)

combined = "\n\n".join(texts)
print(f"Combined text length: {len(combined)} chars")
print(f"Total word_count: {total_wc}")

out = {
    "student_id": "29579",
    "student_text": combined,
    "word_count": total_wc,
}

path = Path("outputs/pilot/29579.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Written to: {path}")
