#!/usr/bin/env python3
"""
Phase 1: Data extraction, validation, and aggregation.
Reads all 689 research JSONs, validates against V1-V8 checks,
cross-references classlists, normalises error counts, and
outputs clean DataFrames for analysis.
"""

import os
import json
import glob
from pathlib import Path
from collections import Counter
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")
RESEARCH_DIR = Path("local-working")
OUTPUT_DIR = Path("outputs/analysis")

REQUIRED_FIELDS_FLAT = [
    "student_id", "class", "error_rate", "word_count",
]
REQUIRED_META_FLAT = [
    "total_edit_count", "overcorrection_count",
    "uncertain_edit_count", "max_span", "avg_span", "multi_token_edits",
]


def load_classlist_supabase() -> dict[str, str]:
    """Load classlist from Supabase -> {student_id: sub_class} (e.g. M2-4A)."""
    mapping = {}
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("WARNING: SUPABASE_URL or SUPABASE_ESL_KEY not set — classlist cross-reference disabled.")
        return mapping
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = client.table("classlists").select("student_id, class").execute()
        for row in result.data:
            mapping[row["student_id"]] = row.get("class", "UNKNOWN")
        print(f"Classlist loaded from Supabase: {len(mapping)} students")
    except Exception as e:
        print(f"WARNING: Could not load classlist from Supabase: {e}")
    return mapping


def extract_record(fp: str) -> dict | None:
    """Read and parse a single research JSON."""
    try:
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"_file": fp, "_error": f"Read/parse error: {e}"}

    record_id = Path(fp).stem.replace("research-", "")
    sid = str(d.get("student_id", ""))
    errant = d.get("errant_analysis", {})
    meta = d.get("metadata", {})
    edits = meta.get("edit_width_stats", {})
    errors_list = errant.get("errors", [])

    return {
        "_file": fp,
        "_record_id": record_id,
        "student_id": sid,
        "name": d.get("name", ""),
        "class": d.get("class", ""),
        "error_rate": d.get("error_rate"),
        "word_count": d.get("word_count"),
        "original_text": d.get("original_text", ""),
        "corrected_text": d.get("corrected_text", ""),
        "summary": d.get("summary", ""),
        "topic": d.get("topic", ""),
        "submission_date": d.get("submission_date", ""),
        "er_type": [e["type"] for e in errors_list],
        "er_count": [e["count"] for e in errors_list],
        "er_example": [e.get("example", "") for e in errors_list],
        "uncategorised": errant.get("uncategorised", []),
        "total_edit_count": meta.get("total_edit_count"),
        "overcorrection_count": meta.get("overcorrection_count"),
        "uncertain_edit_count": meta.get("uncertain_edit_count"),
        "max_span": edits.get("max_span"),
        "avg_span": edits.get("avg_span"),
        "multi_token_edits": edits.get("multi_token_edits"),
    }


def check_required_fields(rec: dict) -> list[str]:
    """V1: Verify required fields are present in flattened record."""
    missing = []
    for field in REQUIRED_FIELDS_FLAT:
        if rec.get(field) is None or rec.get(field) == "":
            missing.append(field)
    for field in REQUIRED_META_FLAT:
        if rec.get(field) is None:
            missing.append(field)
    return missing


def check_structure(rec: dict) -> list[str]:
    """V2: Structural integrity of error lists and metadata."""
    issues = []
    for key in ("er_type", "er_count"):
        val = rec.get(key, [])
        if not isinstance(val, list):
            issues.append(f"{key} is not a list")

    for i, (t, c) in enumerate(zip(rec.get("er_type", []), rec.get("er_count", []))):
        if not isinstance(t, str) or not t:
            issues.append(f"er_type[{i}] invalid")
        if not isinstance(c, int) or c < 0:
            issues.append(f"er_count[{i}]={c} must be non-negative int")

    uncat = rec.get("uncategorised", [])
    if not isinstance(uncat, list):
        issues.append("uncategorised is not a list")

    for key in ("total_edit_count", "overcorrection_count", "uncertain_edit_count"):
        val = rec.get(key)
        if val is not None and (not isinstance(val, int) or val < 0):
            issues.append(f"{key}={val} must be non-negative int")

    return issues


def check_ranges(rec: dict) -> list[str]:
    """V3: Value range checks."""
    issues = []
    er = rec.get("error_rate")
    if er is not None and (not isinstance(er, (int, float)) or er < 0 or er > 100):
        issues.append(f"error_rate={er} out of range [0, 100]")

    wc = rec.get("word_count")
    if wc is not None and (not isinstance(wc, (int, float)) or wc < 1):
        issues.append(f"word_count={wc} out of range [1, inf)")

    tec = rec.get("total_edit_count", 0) or 0
    oc = rec.get("overcorrection_count", 0) or 0
    uc = rec.get("uncertain_edit_count", 0) or 0
    if oc > tec:
        issues.append(f"overcorrection_count={oc} > total_edit_count={tec}")
    if uc > tec:
        issues.append(f"uncertain_edit_count={uc} > total_edit_count={tec}")

    return issues


def check_cohort_consistency(
    recs: list[dict], classlist: dict[str, str]
) -> list[dict]:
    """V4: Cohort assignment cross-reference against classlist."""
    results = []
    for rec in recs:
        sid = rec.get("student_id", "")
        cls = rec.get("class", "")
        in_classlist = sid in classlist
        if cls == "M2" and not in_classlist:
            results.append({
                "student_id": sid,
                "class_in_file": cls,
                "in_classlist": False,
                "issue": "M2 label but student NOT in classlist",
            })
        elif cls == "M3" and in_classlist:
            results.append({
                "student_id": sid,
                "class_in_file": cls,
                "in_classlist": True,
                "issue": "M3 label but student IS in classlist",
            })
    return results


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """V5: Detect true duplicates (same sid + word_count + error_rate)."""
    dup_mask = df.duplicated(subset=["student_id", "word_count", "error_rate"], keep="first")
    return df[dup_mask][["student_id", "word_count", "error_rate", "_record_id"]].copy()


def check_dates(recs: list[dict]) -> list[dict]:
    """V6: Check submission_date format."""
    results = []
    for rec in recs:
        sd = rec.get("submission_date", "")
        if not sd:
            results.append({
                "student_id": rec["student_id"],
                "submission_date": "",
                "issue": "missing",
            })
        else:
            try:
                datetime.fromisoformat(sd.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                results.append({
                    "student_id": rec["student_id"],
                    "submission_date": sd,
                    "issue": "unparseable format",
                })
    return results


def check_delta(rec: dict) -> dict | None:
    """V7: Compute total_edit_count - sum(er_count) - len(uncategorised)."""
    total_edit = rec.get("total_edit_count", 0) or 0
    err_sum = sum(rec.get("er_count", []))
    uncat_len = len(rec.get("uncategorised", []))
    delta = total_edit - err_sum - uncat_len
    if abs(delta) >= 5:
        return {
            "student_id": rec["student_id"],
            "_record_id": rec.get("_record_id"),
            "total_edit_count": total_edit,
            "sum_error_counts": err_sum,
            "len_uncategorised": uncat_len,
            "delta": delta,
        }
    return None


def build_error_type_frame(recs: list[dict]) -> pd.DataFrame:
    """Build a per-file, per-error-type long-form DataFrame
    with normalised counts (errors per 100 words)."""
    rows = []
    for rec in recs:
        sid = rec["student_id"]
        wid = rec["_record_id"]
        cls = rec["class"]
        wc = rec.get("word_count", 1) or 1
        types = rec.get("er_type", [])
        counts = rec.get("er_count", [])
        for err_type, raw_count in zip(types, counts):
            norm = round(raw_count / wc * 100, 4)
            rows.append({
                "student_id": sid,
                "record_id": wid,
                "class": cls,
                "word_count": wc,
                "error_type": err_type,
                "count": raw_count,
                "count_per_100w": norm,
            })
    return pd.DataFrame(rows)


def normalise_error_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise error counts to per 100 words in wide format."""
    if df.empty:
        return df
    for col in df.columns:
        if col.startswith("err_"):
            wc = df["word_count"].replace(0, 1)
            df[f"{col}_per100w"] = (df[col] / wc * 100).round(4)
    return df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    classlist = load_classlist_supabase()

    files = sorted(glob.glob(str(RESEARCH_DIR / "research-*.json")))
    print(f"Research files found: {len(files)}")

    records = []
    errors = []
    for fp in files:
        rec = extract_record(fp)
        if "_error" in rec:
            errors.append(rec)
        else:
            records.append(rec)

    print(f"Parsed successfully: {len(records)}")
    print(f"Parse errors: {len(errors)}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e['_file']}: {e['_error']}")

    # --- Validation ---
    validation_results = {
        "V1_required_field_issues": [],
        "V2_structure_issues": [],
        "V3_range_issues": [],
    }

    v1_total = 0
    v2_total = 0
    v3_total = 0
    for rec in records:
        v1 = check_required_fields(rec)
        v2 = check_structure(rec)
        v3 = check_ranges(rec)
        if v1:
            validation_results["V1_required_field_issues"].append({
                "student_id": rec["student_id"],
                "record_id": rec.get("_record_id"),
                "missing": v1,
            })
            v1_total += 1
        if v2:
            validation_results["V2_structure_issues"].append({
                "student_id": rec["student_id"],
                "record_id": rec.get("_record_id"),
                "issues": v2,
            })
            v2_total += 1
        if v3:
            validation_results["V3_range_issues"].append({
                "student_id": rec["student_id"],
                "record_id": rec.get("_record_id"),
                "issues": v3,
            })
            v3_total += 1

    print("\n=== VALIDATION RESULTS ===")
    print(f"V1 (field completeness): {v1_total}/{len(records)} files with issues")
    print(f"V2 (structural integrity): {v2_total}/{len(records)} files with issues")
    print(f"V3 (value ranges): {v3_total}/{len(records)} files with issues")

    # V4 — cohort assignment
    v4_results = check_cohort_consistency(records, classlist)
    print(f"V4 (cohort consistency): {len(v4_results)} anomalies")
    for r in v4_results:
        print(f"  {r['student_id']}: {r['issue']}")

    # V5 — duplicates
    df_flat = pd.DataFrame(records)
    dupes = check_duplicates(df_flat)
    print(f"V5 (duplicates): {len(dupes)} exact-duplicate rows detected")
    if not dupes.empty:
        print(dupes.to_string(index=False))

    # V6 — dates
    v6_results = check_dates(records)
    missing_dates = [r for r in v6_results if r["issue"] == "missing"]
    bad_dates = [r for r in v6_results if r["issue"] != "missing"]
    print(f"V6 (dates): {len(missing_dates)} missing, {len(bad_dates)} unparseable")

    # V7 — delta
    deltas = []
    for rec in records:
        d = check_delta(rec)
        if d:
            deltas.append(d)
    print(f"V7 (edit-count delta): {len(deltas)} files with |delta| >= 5")
    for d in sorted(deltas, key=lambda x: -abs(x["delta"])):
        print(f"  {d['student_id']} ({d['_record_id']}): delta={d['delta']}")

    # V8 — topic inventory
    topics = Counter()
    for rec in records:
        t = rec.get("topic", "") or ""
        topics[t] += 1
    print(f"\nV8 (topic inventory): {len(topics)} unique topic values")
    for t, cnt in topics.most_common():
        print(f"  [{cnt:3d}] {t}")

    # ---- Aggregated output ----
    print("\n=== AGGREGATING ===")

    # Wide-format error-type matrix
    et_long = build_error_type_frame(records)
    et_wide = et_long.pivot_table(
        index=["student_id", "record_id", "class", "word_count"],
        columns="error_type",
        values="count",
        fill_value=0,
    ).reset_index()
    et_wide.columns.name = None
    et_wide.columns = [f"err_{c}" if c not in ("student_id", "record_id", "class", "word_count") else c for c in et_wide.columns]
    et_wide = normalise_error_counts(et_wide)

    # Merge flat fields with error-type matrix
    meta_cols = [
        "name", "error_rate", "summary", "topic", "submission_date",
        "total_edit_count", "overcorrection_count", "uncertain_edit_count",
        "max_span", "avg_span", "multi_token_edits", "word_count",
    ]
    df_meta = df_flat[["student_id", "_record_id", *meta_cols]].rename(
        columns={"_record_id": "record_id"}
    )

    # Add sub_class from classlist
    df_meta["sub_class"] = df_meta["student_id"].map(classlist).fillna("")

    df_merged = df_meta.merge(et_wide, on=["student_id", "record_id", "word_count"], how="left")

    # Per-student summary
    student_summary = df_merged.groupby("student_id").agg(
        class_label=("class", "first"),
        sub_class=("sub_class", "first"),
        name=("name", "first"),
        n_submissions=("record_id", "count"),
        mean_error_rate=("error_rate", "mean"),
        mean_word_count=("word_count", "mean"),
        total_word_count=("word_count", "sum"),
    ).reset_index()

    # ---- Write outputs ----
    print(f"\nWriting outputs to {OUTPUT_DIR}/")

    df_merged.to_parquet(OUTPUT_DIR / "by_file.parquet", index=False)
    df_merged.to_csv(OUTPUT_DIR / "by_file.csv", index=False)
    student_summary.to_parquet(OUTPUT_DIR / "by_student.parquet", index=False)
    student_summary.to_csv(OUTPUT_DIR / "by_student.csv", index=False)
    et_long.to_parquet(OUTPUT_DIR / "by_file_long.parquet", index=False)
    et_long.to_csv(OUTPUT_DIR / "by_file_long.csv", index=False)

    # Validation report
    report = {
        "n_files_total": len(files),
        "n_files_parsed": len(records),
        "n_files_errors": len(errors),
        "n_unique_students": df_merged["student_id"].nunique(),
        "v1_missing_fields": v1_total,
        "v2_structure_issues": v2_total,
        "v3_range_issues": v3_total,
        "v4_cohort_anomalies": len(v4_results),
        "v4_anomaly_details": v4_results,
        "v5_duplicates": len(dupes),
        "v5_duplicate_rows": dupes.to_dict("records") if not dupes.empty else [],
        "v6_missing_dates": len(missing_dates),
        "v6_bad_dates": len(bad_dates),
        "v7_high_delta_files": len(deltas),
        "v7_delta_details": deltas,
        "v8_unique_topics": len(topics),
        "v8_topic_inventory": [{"topic": t, "count": c} for t, c in topics.most_common()],
    }

    with open(OUTPUT_DIR / "validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nDone. Files written:")
    print(f"  {OUTPUT_DIR / 'by_file.csv'}")
    print(f"  {OUTPUT_DIR / 'by_file.parquet'}")
    print(f"  {OUTPUT_DIR / 'by_file_long.csv'}")
    print(f"  {OUTPUT_DIR / 'by_file_long.parquet'}")
    print(f"  {OUTPUT_DIR / 'by_student.csv'}")
    print(f"  {OUTPUT_DIR / 'by_student.parquet'}")
    print(f"  {OUTPUT_DIR / 'validation_report.json'}")

    # Brief summary
    print("\n=== DATASET SUMMARY ===")
    print(f"Students: {student_summary['n_submissions'].sum()} submissions from {len(student_summary)} students")
    print(f"  M2 (active): {len(student_summary[student_summary['class_label'] == 'M2'])} students, "
          f"{student_summary[student_summary['class_label'] == 'M2']['n_submissions'].sum()} submissions")
    print(f"  M3 (former): {len(student_summary[student_summary['class_label'] == 'M3'])} students, "
          f"{student_summary[student_summary['class_label'] == 'M3']['n_submissions'].sum()} submissions")
    print(f"Mean error rate: M2={student_summary[student_summary['class_label'] == 'M2']['mean_error_rate'].mean():.2f}%, "
          f"M3={student_summary[student_summary['class_label'] == 'M3']['mean_error_rate'].mean():.2f}%")
    print(f"Mean word count: M2={student_summary[student_summary['class_label'] == 'M2']['mean_word_count'].mean():.0f}, "
          f"M3={student_summary[student_summary['class_label'] == 'M3']['mean_word_count'].mean():.0f}")


if __name__ == "__main__":
    main()
