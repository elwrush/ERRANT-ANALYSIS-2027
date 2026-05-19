#!/usr/bin/env python3
"""Fetch sampled records from Supabase writing_assessment_cambridge table, write per-record JSONs."""
import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_ESL_KEY must be set")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = Path("outputs/research")
SAMPLING_PLAN = Path("local-working/sampling_plan.json")
MIN_WORDS = 40


def clean_html(text: str) -> str:
    """Strip <br> and other HTML tags from text."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text


def count_words(text: str) -> int:
    return len(text.split())


def build_record_id(student_id: str, submission_date: str) -> str:
    """Construct a unique record_id from the composite primary key."""
    # Use just the date portion (strip timezone) for readability
    date_part = submission_date.split("T")[0] if submission_date else "unknown"
    return f"{student_id}_{date_part}"


def main():
    # Load sampling plan
    plan = json.loads(SAMPLING_PLAN.read_text(encoding="utf-8"))
    m2_ids = plan["cohorts"]["M2"]["sampled_student_ids"]
    m3_ids = plan["cohorts"]["M3"]["sampled_student_ids"]

    # Build cohort mapping
    student_cohort = {}
    for sid in m2_ids:
        student_cohort[sid] = "M2"
    for sid in m3_ids:
        student_cohort[sid] = "M3"

    # Get current classlist info (name, class)
    cls = client.table("classlists").select("student_id, name, class").execute()
    classlist_info = {r["student_id"]: r for r in cls.data}

    # Get all sampled student IDs combined (for single-query fetch)
    all_ids = list(student_cohort.keys())

    # Fetch all writing records for sampled students from writing_assessment_cambridge
    all_recs = client.table("writing_assessment_cambridge").select("*")\
        .in_("student_id", all_ids)\
        .order("submission_date")\
        .execute()

    print(f"Sampled students: {len(all_ids)}")
    print(f"Total records fetched: {len(all_recs.data)}")

    written = 0
    skipped = 0
    total_words = 0
    total_records = len(all_recs.data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for rec in all_recs.data:
        sid = rec["student_id"]
        cohort = student_cohort.get(sid, "M3")
        text = rec.get("student_text") or ""
        cleaned = clean_html(text)
        wc = count_words(cleaned)

        if wc < MIN_WORDS:
            skipped += 1
            continue

        # Determine name and class
        if cohort == "M2":
            info = classlist_info.get(sid, {})
            name = info.get("name", sid)
            cls_label = "M2"
        else:
            name = sid
            cls_label = "M3"

        total_words += wc

        record_id = build_record_id(sid, rec.get("submission_date", ""))

        out = {
            "student_id": sid,
            "record_id": record_id,
            "submission_date": rec.get("submission_date", ""),
            "academic_year": rec.get("academic_year"),
            "topic": rec.get("topic", ""),
            "student_text": cleaned,
            "word_count": wc,
            "name": name,
            "class": cls_label,
            "cefr": rec.get("cefr"),
            "assessment_type": rec.get("assessment_type"),
            "exam_type": rec.get("exam_type"),
            "task": rec.get("task"),
            "overall_score": rec.get("overall_score"),
            "content_score": rec.get("content_score"),
            "communicative_achievement_score": rec.get("communicative_achievement_score"),
            "organisation_score": rec.get("organisation_score"),
            "language_score": rec.get("language_score"),
        }

        out_path = OUTPUT_DIR / f"{record_id}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1

    print("\n=== Summary ===")
    print(f"  Total records in table for sampled students: {total_records}")
    print(f"  Records written: {written}")
    print(f"  Records skipped (< {MIN_WORDS} words): {skipped}")
    print(f"  Total words across all records: {total_words}")
    print(f"  Output: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
