#!/usr/bin/env python3
"""
Sampling strategy for writing error analysis.

Strategy:
  - M2 cohort (36 students, 289 records): analyze ALL students and ALL records.
    The student population is small enough that sampling would lose information
    without meaningful savings.
  - M3 cohort (61 students, 689 records): randomly select 36 students
    (matched to M2 size for balanced comparison). This avoids clustering
    effects (Gries 2021) while giving equivalent student-level representation.

Rationale:
  - Student is the sampling unit (not individual records), because records
    from the same student are not independent.
  - Matching sample sizes enables cleaner cohort comparisons.
  - 36 students per cohort exceeds the "min 20-30" threshold from published
    learner corpus studies.
"""
import os
import sys
import json
import random
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_ESL_KEY must be set")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)
SEED = 42
random.seed(SEED)

OUTPUT = Path("local-working/sampling_plan.json")
M3_SAMPLE_SIZE = 36

# ── Step 1: Get current classlist ──────────────────────────────────────
cls = client.table("classlists").select("student_id").execute()
classlist_ids = {r["student_id"] for r in cls.data}

# ── Step 2: Get all writing records ────────────────────────────────────
# Fetch in batches if needed (table has 978 rows, under default 1000 limit)
all_writing = client.table("student_submissions").select("*").ilike("skill", "Writing").execute()

# Group records by student and assign cohort
m2_records = []   # students currently in classlists (wrote when M2)
m3_records = []   # students NOT in classlists (wrote when M3)
m2_students = defaultdict(list)
m3_students = defaultdict(list)

for row in all_writing.data:
    sid = row["student_id"]
    if sid in classlist_ids:
        m2_students[sid].append(row)
        m2_records.append(row)
    else:
        m3_students[sid].append(row)
        m3_records.append(row)

# ── Step 3: Sampling ────────────────────────────────────────────────────
# M2: all students, all records
m2_selected_students = sorted(m2_students.keys())
m2_selected_records = m2_records

# M3: randomly select M3_SAMPLE_SIZE students, take all their records
m3_all_students = sorted(m3_students.keys())
m3_selected_students = sorted(random.sample(m3_all_students, min(M3_SAMPLE_SIZE, len(m3_all_students))))
m3_selected_records = []
for sid in m3_selected_students:
    m3_selected_records.extend(m3_students[sid])

# ── Step 4: Report ──────────────────────────────────────────────────────
m2_record_count = sum(len(v) for v in m2_students.values())
m3_selected_record_count = len(m3_selected_records)
m3_total_records = sum(len(v) for v in m3_students.values())

plan = {
    "seed": SEED,
    "strategy": "M2: all students. M3: random students (balanced to M2 count).",
    "rationale": "Student is sampling unit to avoid pseudoreplication (Gries 2021). Balanced sizes enable clean cohort comparison.",
    "cohorts": {
        "M2": {
            "total_students": len(m2_students),
            "total_records": m2_record_count,
            "sampled_students": len(m2_selected_students),
            "sampled_records": m2_record_count,
            "sampled_student_ids": m2_selected_students,
            "note": "All students sampled (small population)."
        },
        "M3": {
            "total_students": len(m3_students),
            "total_records": m3_total_records,
            "sampled_students": len(m3_selected_students),
            "sampled_records": m3_selected_record_count,
            "sampled_student_ids": m3_selected_students,
            "note": f"Random sample of {M3_SAMPLE_SIZE} from {len(m3_students)} students."
        }
    }
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

print("=== Sampling Strategy ===")
print()
print("Cohort assignment:")
print("  M2 = in current classlists (wrote when M2)")
print("  M3 = NOT in current classlists (graduated, wrote when M3)")
print()
print(f"{'':>6} | {'Students':>10} | {'Records':>10} | {'Sampled':>10} | {'Sampled':>10}")
print(f"{'':>6} | {'(total)':>10} | {'(total)':>10} | {'students':>10} | {'records':>10}")
print("-" * 56)
print(f"{'M2':>6} | {len(m2_students):>10} | {m2_record_count:>10} | {len(m2_selected_students):>10} | {m2_record_count:>10}")
print(f"{'M3':>6} | {len(m3_students):>10} | {m3_total_records:>10} | {len(m3_selected_students):>10} | {m3_selected_record_count:>10}")
print("-" * 56)
print(f"{'Total':>6} | {len(m2_students)+len(m3_students):>10} | {m2_record_count+m3_total_records:>10} | {len(m2_selected_students)+len(m3_selected_students):>10} | {m2_record_count+m3_selected_record_count:>10}")
print()
print(f"Sampling plan saved to: {OUTPUT}")
