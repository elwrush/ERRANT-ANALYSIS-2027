#!/usr/bin/env python3
"""Batch ERRANT error analysis for migrated records — error counts only, no summaries.

Reads records from error_reports WHERE error_percent IS NULL,
runs correction + ERRANT annotation, upserts error counts back.
"""
import os
import sys
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

load_dotenv()

from errant_analysis import (
    correct_text,
    classify_edits,
    pre_split_edits,
    ERRANT_CODE_TO_COLUMN,
    ERROR_CODE_COLUMNS,
)


def is_fluency_rewrite(original, corrected, word_count, total_errors):
    """Deterministic check — flags fluency rewrites before ERRANT annotation.
    
    Returns True if the correction appears to be a fluency rewrite rather than
    a minimal edit. Uses three string-based heuristics, no model calls.
    """
    if not original or not corrected:
        return False
    
    # Check 1: Text length expansion (>1.3x) — fluency rewrites add explanatory content
    if len(corrected) / len(original) > 1.3:
        return True
    
    # Check 2: Edit density — more than 1 edit per word is near-certain fluency rewrite
    if word_count > 0 and total_errors / word_count > 1.0:
        return True
    
    # Check 3: Sentence splitting — fluency rewrites break run-ons into tidy sentences
    orig_sentences = len(re.split(r'[.!?]+', original))
    corr_sentences = len(re.split(r'[.!?]+', corrected))
    if orig_sentences > 0 and corr_sentences / orig_sentences > 2.0:
        return True
    
    return False


def process_one_record(student_text, word_count, nlp, annotator, max_attempts=3):
    student_text = student_text.strip()
    if not student_text:
        return None, None

    orig_text = student_text

    corrected = None
    total_errors_estimate = 0
    
    for attempt in range(max_attempts):
        corrected, _, _ = correct_text(orig_text, nlp)
        corrected = corrected.strip()
        
        if orig_text == corrected:
            return 0, {col: 0 for col in ERROR_CODE_COLUMNS}
        
        # Quick pre-check: estimate error count from ERRANT to check for fluency rewrite
        orig_parse = annotator.parse(orig_text)
        cor_parse = annotator.parse(corrected)
        edits = annotator.annotate(orig_parse, cor_parse)
        word_count_actual = max(word_count, len(orig_text.split()))
        total_errors_estimate = len(edits)
        
        if not is_fluency_rewrite(orig_text, corrected, word_count_actual, total_errors_estimate):
            break  # good result — proceed with full annotation
        
        if attempt < max_attempts - 1:
            print(f"  Fluency rewrite detected (attempt {attempt + 1}), retrying...")
    
    # Full ERRANT annotation on the final (good or best-available) result
    counts = {col: 0 for col in ERROR_CODE_COLUMNS}
    orig_parse = annotator.parse(orig_text)
    cor_parse = annotator.parse(corrected)
    edits = annotator.annotate(orig_parse, cor_parse)
    edits = pre_split_edits(annotator, edits, orig_parse, cor_parse)

    errors_list, _, _ = classify_edits(
        edits,
        orig_tokens=[t.text for t in orig_parse],
        cor_tokens=[t.text for t in cor_parse],
    )

    for eg in errors_list:
        col = ERRANT_CODE_TO_COLUMN.get(eg["type"])
        if col:
            counts[col] = eg["count"]

    correction_count = sum(eg["count"] for eg in errors_list)
    if word_count > 0 and word_count < 40:
        error_rate = None
    else:
        error_rate = round(correction_count / word_count * 100) if word_count > 0 else 0

    return error_rate, counts


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ESL_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_ESL_KEY must be set")
        sys.exit(1)

    client = create_client(url, key)

    # 1. Get records needing analysis
    print("Querying error_reports for records needing analysis...")
    result = (
        client.table("error_reports")
        .select("student_id, date, word_count")
        .filter("error_percent", "is", "null")
        .execute()
    )
    pending = result.data
    print(f"  Found {len(pending)} records")

    if not pending:
        print("  Nothing to do.")
        return

    # 2. Fetch student_text from student_submissions
    print("Fetching student_text from student_submissions...")
    ss_result = (
        client.table("student_submissions")
        .select("student_id, submission_date, student_text")
        .in_("skill", ["Writing", "writing"])
        .execute()
    )

    text_lookup = {}
    for r in ss_result.data:
        sid = str(r["student_id"])
        date_part = str(r.get("submission_date", ""))[:10]
        text = r.get("student_text")
        if sid and date_part and text:
            text_lookup[(sid, date_part)] = text

    to_process = []
    missing = 0
    for r in pending:
        sid = str(r["student_id"])
        d = str(r["date"])
        key = (sid, d)
        if key in text_lookup:
            to_process.append({
                "student_id": sid,
                "date": d,
                "word_count": r.get("word_count") or 0,
                "student_text": text_lookup[key],
            })
        else:
            missing += 1

    print(f"  Records with text available: {len(to_process)}")
    if missing:
        print(f"  WARNING: {missing} records have no matching student_text (skipped)")

    if not to_process:
        print("  Nothing to process.")
        return

    CHECKPOINT_FILE = Path("local-working/batch_errant_results.json")

    # Check if processing results already saved (resume from checkpoint)
    results = []
    if CHECKPOINT_FILE.exists():
        print(f"  Found checkpoint file — loading {CHECKPOINT_FILE}...")
        results = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        print(f"  Loaded {len(results)} results from checkpoint.")

    if not results:
        # 3. Load spacy + ERRANT
        print("Loading spacy and ERRANT...")
        import spacy
        import errant

        nlp = spacy.load("en_core_web_sm")
        annotator = errant.load("en")

        # 4. Process each record
        print(f"\nProcessing {len(to_process)} records (this will take ~45 minutes)...")
        for rec in tqdm(to_process, desc="ERRANT analysis", unit="rec"):
            try:
                error_rate, counts = process_one_record(
                    rec["student_text"], rec["word_count"], nlp, annotator
                )
                if counts is not None:
                    row = {
                        "student_id": rec["student_id"],
                        "date": rec["date"],
                        "error_percent": error_rate,
                    }
                    row.update(counts)
                    results.append(row)
                else:
                    tqdm.write(f"  SKIPPED (empty text): {rec['student_id']}/{rec['date']}")
            except Exception as e:
                tqdm.write(f"  ERROR: {rec['student_id']}/{rec['date']}: {e}")
                continue

        if results:
            CHECKPOINT_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  Saved {len(results)} results to checkpoint ({CHECKPOINT_FILE})")

    if not results:
        print("\nNo results to upsert.")
        return

    # Fetch existing error_reports rows to supply NOT NULL columns for upsert
    print(f"Fetching existing error_reports data...")
    all_existing = client.table("error_reports").select("*").execute().data
    existing_map = {(str(r["student_id"]), str(r["date"])): r for r in all_existing}

    full_rows = []
    missing_existing = 0
    for r in results:
        key = (r["student_id"], r["date"])
        existing_row = existing_map.get(key)
        if not existing_row:
            missing_existing += 1
            continue
        full = dict(existing_row)
        full["error_percent"] = r.get("error_percent")
        for col in ERROR_CODE_COLUMNS:
            full[col] = r.get(col, 0)
        full_rows.append(full)

    if missing_existing:
        print(f"  WARNING: {missing_existing} records not found in error_reports (skipped)")

    BATCH_SIZE = 100
    total_upserted = 0
    print(f"Upserting {len(full_rows)} results to error_reports...")
    for i in range(0, len(full_rows), BATCH_SIZE):
        batch = full_rows[i : i + BATCH_SIZE]
        try:
            client.table("error_reports").upsert(batch, on_conflict="student_id,date").execute()
            total_upserted += len(batch)
            tqdm.write(
                f"  Batch {i // BATCH_SIZE + 1}/{(len(full_rows) - 1) // BATCH_SIZE + 1}: "
                f"{len(batch)} rows ({total_upserted}/{len(full_rows)})"
            )
        except Exception as e:
            tqdm.write(f"  UPSERT ERROR on batch {i // BATCH_SIZE + 1}: {e}")

    if total_upserted == len(full_rows) and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print(f"  Checkpoint file removed (all upserts completed).")

    # 5. Report
    print("\n=== FINAL REPORT ===")
    remaining = (
        client.table("error_reports")
        .select("id", count="exact")
        .filter("error_percent", "is", "null")
        .execute()
    )
    remaining_count = getattr(remaining, "count", len(remaining.data))
    print(f"  Processed:  {len(results)}")
    print(f"  Upserted:   {total_upserted}")
    print(f"  Still NULL: {remaining_count}")
    if remaining_count == 0:
        print("  Status: COMPLETE — all migrated records have error counts.")
    else:
        print(f"  Status: {remaining_count} records still pending.")

    # Spot-check
    spot = (
        client.table("error_reports")
        .select("student_id, date, error_percent, r_verb_tense, r_det, r_prep, r_spell")
        .order("id", desc=True)
        .limit(5)
        .execute()
    )
    print("\n  Sample processed records (latest 5):")
    for row in spot.data:
        print(
            f"    sid={row['student_id']} date={row.get('date')} "
            f"err%={row.get('error_percent')} "
            f"r_verb_tense={row.get('r_verb_tense', 0)} "
            f"r_det={row.get('r_det', 0)} "
            f"r_prep={row.get('r_prep', 0)} "
            f"r_spell={row.get('r_spell', 0)}"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
