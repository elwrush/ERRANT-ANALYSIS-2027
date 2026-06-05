#!/usr/bin/env python3
"""Migrate writing records from student_submissions to error_reports.

Three-layer safety:
  Layer 1 — Local JSON dump of existing error_reports
  Layer 2 — Supabase clone table (if Management API available)
  Layer 3 — Pre-insert deduplication against (student_id, date) pairs

Usage:
    python src/migrate_writing_records.py           # full migration
    python src/migrate_writing_records.py --dry-run   # preview only
    python src/migrate_writing_records.py --skip-backup  # skip backup layers
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ERROR_CODE_COLUMNS = [
    "r_noun", "r_noun_num", "r_noun_poss", "r_noun_infl",
    "r_verb", "r_verb_tense", "r_verb_sva", "r_verb_form", "r_verb_infl",
    "r_adj", "r_adj_form", "r_adv", "r_prep", "r_pron", "r_det",
    "r_conj", "r_part", "r_punct", "r_spell", "r_orth", "r_morph",
    "r_wo", "r_contr",
    "m_noun", "m_noun_num", "m_verb", "m_verb_tense", "m_verb_form",
    "m_prep", "m_pron", "m_det", "m_conj", "m_part", "m_punct",
    "u_noun", "u_verb", "u_prep", "u_pron", "u_det", "u_conj", "u_part",
    "u_punct",
    "other", "unk",
]


def get_project_ref():
    url = os.environ.get("SUPABASE_URL", "")
    if not url:
        return None
    return url.split("//")[1].split(".")[0]


def layer1_local_backup(client, output_dir, dry_run=False):
    print("\n=== Layer 1: Local JSON backup of error_reports ===")
    result = client.table("error_reports").select("*").order("id").execute()
    records = result.data
    count = len(records)
    print(f"  Found {count} existing error_reports records")

    if dry_run:
        return records, count

    backup_path = (
        Path(output_dir)
        / f"backup_error_reports_{datetime.now().strftime('%Y-%m-%d')}.json"
    )
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(
        json.dumps(records, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Saved to: {backup_path}")
    return records, count


def layer2_clone_table(dry_run=False):
    print("\n=== Layer 2: Supabase clone table (error_reports_backup) ===")
    access_token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    project_ref = get_project_ref()

    if not access_token:
        print("  SKIPPED: SUPABASE_ACCESS_TOKEN not set")
        print("  Fallback: Layer 1 local JSON is sufficient for rollback")
        return

    if not project_ref:
        print("  SKIPPED: Could not extract project ref from SUPABASE_URL")
        return

    if dry_run:
        print("  Would create: error_reports_backup table (dry-run)")
        return

    import requests

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    queries = [
        "DROP TABLE IF EXISTS error_reports_backup",
        "CREATE TABLE error_reports_backup AS SELECT * FROM error_reports",
    ]
    for q in queries:
        resp = requests.post(
            f"https://api.supabase.com/v1/projects/{project_ref}/database/query",
            headers=headers,
            json={"query": q},
            timeout=30,
        )
        if resp.status_code >= 400:
            print(f"  WARNING: API query failed ({resp.status_code}): {resp.text[:200]}")
            print("  Fallback: Layer 1 local JSON backup still available")
            return
    print("  Created: error_reports_backup (full clone of error_reports)")


def get_classlist_data(client):
    result = client.table("classlists").select("student_id, name").execute()
    ids = set()
    names = {}
    for r in result.data:
        sid = r["student_id"]
        ids.add(sid)
        names[sid] = r.get("name", "")
    return ids, names


def get_existing_pairs(client):
    result = client.table("error_reports").select("student_id, date").execute()
    pairs = set()
    for r in result.data:
        sid = r.get("student_id")
        d = r.get("date")
        if sid is not None and d is not None:
            pairs.add((str(sid), str(d)))
    return pairs


def get_writing_records(client):
    all_records = (
        client.table("student_submissions")
        .select("id, student_id, submission_date, student_text, word_count, academic_year")
        .in_("skill", ["Writing", "writing"])
        .execute()
    )
    return [r for r in all_records.data if r.get("student_text")]


def build_insert_rows(records, classlist_ids, classlist_names, existing_pairs):
    rows = []
    skipped = 0
    duplicate_in_source = 0
    no_date = 0
    m2_count = 0
    m3_count = 0
    seen_this_run = set()

    for r in records:
        sid = str(r["student_id"])
        date_raw = r.get("submission_date", "")
        date_str = str(date_raw)[:10] if date_raw else ""

        if not date_str:
            no_date += 1
            continue

        if (sid, date_str) in existing_pairs:
            skipped += 1
            continue

        pair = (sid, date_str)
        if pair in seen_this_run:
            duplicate_in_source += 1
            continue
        seen_this_run.add(pair)

        is_m2 = sid in classlist_ids
        if is_m2:
            m2_count += 1
        else:
            m3_count += 1

        row = {
            "student_id": sid,
            "class": "M2" if is_m2 else "M3",
            "name": classlist_names.get(sid, ""),
            "summary": r.get("student_text") or "",
            "word_count": r.get("word_count") or 0,
            "academic_year": r.get("academic_year"),
            "date": date_str,
            "error_percent": None,
        }
        for col in ERROR_CODE_COLUMNS:
            row[col] = 0

        rows.append(row)

    return rows, skipped, duplicate_in_source, no_date, m2_count, m3_count


def main():
    parser = argparse.ArgumentParser(
        description="Migrate writing records from student_submissions to error_reports"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    parser.add_argument("--skip-backup", action="store_true", help="Skip Layer 1 and Layer 2 backups")
    parser.add_argument("--output-dir", default="local-working", help="Directory for backup files")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ESL_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_ESL_KEY must be set")
        sys.exit(1)

    from supabase import create_client

    client = create_client(url, key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Writing Records Migration — {ts}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE'}")

    # === Step 1: Backup layers ===
    if args.skip_backup:
        result = client.table("error_reports").select("id", count="exact").execute()
        backup_count_before = getattr(result, "count", len(result.data))
    else:
        _, backup_count_before = layer1_local_backup(client, output_dir, args.dry_run)
        layer2_clone_table(args.dry_run)

    print(f"\nExisting error_reports count: {backup_count_before}")

    # === Step 2: Load reference data ===
    print("\n=== Loading reference data ===")
    classlist_ids, classlist_names = get_classlist_data(client)
    existing_pairs = get_existing_pairs(client)
    print(f"  Classlist entries: {len(classlist_ids)}")
    print(f"  Existing (student_id, date) pairs: {len(existing_pairs)}")

    # === Step 3: Fetch writing records ===
    print("\n=== Fetching writing records ===")
    records = get_writing_records(client)
    print(f"  Writing records with student_text: {len(records)}")

    # === Step 4: Build insert rows ===
    print("\n=== Processing records ===")
    insert_rows, skipped, duplicate_in_source, no_date, m2_count, m3_count = build_insert_rows(
        records, classlist_ids, classlist_names, existing_pairs
    )

    print(f"  To insert:  {len(insert_rows)}")
    print(f"  Skipped (already in error_reports): {skipped}")
    print(f"  Skipped (duplicate in source data): {duplicate_in_source}")
    print(f"  Skipped (no date): {no_date}")
    print(f"  M2 (in classlist): {m2_count}")
    print(f"  M3 (not in classlist): {m3_count}")

    # === Step 5: Insert or dry-run ===
    if args.dry_run:
        print("\n=== DRY RUN — no inserts performed ===")
        print(f"  Would insert {len(insert_rows)} rows")
        print(f"  New error_reports total would be: {backup_count_before + len(insert_rows)}")
        if insert_rows:
            print("\nSample rows (first 5):")
            for row in insert_rows[:5]:
                sl = len(row.get("summary", ""))
                print(f"  sid={row['student_id']} date={row['date']} class={row['class']} name={row['name']} summary={sl}chars")
        return

    if not insert_rows:
        print("\n=== Nothing to insert ===")
        return

    BATCH_SIZE = 100
    total_inserted = 0

    print(f"\n=== Inserting {len(insert_rows)} rows ===")
    for i in range(0, len(insert_rows), BATCH_SIZE):
        batch = insert_rows[i : i + BATCH_SIZE]
        try:
            client.table("error_reports").insert(batch).execute()
            total_inserted += len(batch)
            print(f"  Batch {i // BATCH_SIZE + 1}/{(len(insert_rows) - 1) // BATCH_SIZE + 1}: {len(batch)} rows ({total_inserted}/{len(insert_rows)})")
        except Exception as e:
            print(f"  ERROR on batch {i // BATCH_SIZE + 1}: {e}")
            print(f"  Stopping. {total_inserted} rows inserted before error.")
            break

    # === Step 6: Verification ===
    print("\n=== POST-MIGRATION VERIFICATION ===")
    result_after = client.table("error_reports").select("*", count="exact").execute()
    count_after = getattr(result_after, "count", len(result_after.data))
    print(f"  error_reports BEFORE: {backup_count_before}")
    print(f"  error_reports AFTER:  {count_after}")
    print(f"  Inserted:              {total_inserted}")

    if count_after != backup_count_before + total_inserted:
        print(f"  WARNING: Count mismatch! Expected {backup_count_before + total_inserted}")

    spot = (
        client.table("error_reports")
        .select("student_id, class, name, date, summary, word_count, error_percent")
        .order("id", desc=True)
        .limit(5)
        .execute()
    )
    print("\n  Latest 5 rows in error_reports:")
    for row in spot.data:
        prev = (row.get("summary") or "")[:60]
        print(f"    sid={row['student_id']} date={row.get('date')} class={row.get('class')} name={row.get('name')} wc={row.get('word_count')} err%={row.get('error_percent')} summary=\"{prev}...\"")

    print("\nDone.")


if __name__ == "__main__":
    main()
