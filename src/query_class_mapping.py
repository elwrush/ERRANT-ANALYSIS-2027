#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: missing env vars")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Get all students from classlists with their class
cls = client.table("classlists").select("student_id, class").execute()
classlist = {r["student_id"]: r["class"] for r in cls.data}
classes = Counter(r["class"] for r in cls.data)
print("=== classlists distribution ===")
for c, n in sorted(classes.items()):
    print(f"  {c}: {n}")
print(f"  total: {len(classlist)}")

# 2. Get all distinct student_ids in writing_assessment_cambridge
subs = client.table("writing_assessment_cambridge").select("student_id", count="exact").execute()
sub_ids = {r["student_id"] for r in subs.data}

print("\n=== writing_assessment_cambridge ===")
print(f"  distinct students: {len(sub_ids)}")
print(f"  total rows: {subs.count}")

# 3. Cross-reference
in_class = sub_ids & set(classlist.keys())
not_in_class = sub_ids - set(classlist.keys())
print("\n=== Cross-reference ===")
print(f"  in classlists: {len(in_class)}")
print(f"  NOT in classlists: {len(not_in_class)}")

# 4. For those in classlists, what classes are they?
in_class_classes = Counter(classlist[sid] for sid in in_class)
print(f"  class breakdown: {dict(in_class_classes)}")

# 5. For those NOT in classlists, just show count
print("\n=== Absent from classlists (M3) ===")
print(f"  count: {len(not_in_class)}")
if not_in_class:
    print(f"  sample: {sorted(not_in_class)[:10]}")
