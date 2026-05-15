#!/usr/bin/env python3
import os
import sys
import csv
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")

STUDENTS_PATH = Path("docs/students.txt")
TABLE_NAME = "classlists"


def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_ESL_KEY must be set in environment")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def parse_students(path: Path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        if header is None:
            print(f"Error: {path} is empty")
            sys.exit(1)
        for line_num, cols in enumerate(reader, 2):
            if len(cols) < 3:
                print(f"Warning: line {line_num} has only {len(cols)} columns, skipping")
                continue
            class_name = cols[0].strip()
            student_id = cols[1].strip()
            name = cols[2].strip()
            if not student_id:
                print(f"Warning: line {line_num} has empty student_ID, skipping")
                continue
            rows.append({
                "student_id": student_id,
                "name": name,
                "class": class_name,
            })
    return rows


def delete_all(client: Client) -> int:
    try:
        result = client.table(TABLE_NAME).delete().neq("student_id", "").execute()
        deleted = len(result.data)
        print(f"  Deleted {deleted} existing record(s)")
        return deleted
    except Exception as e:
        print(f"  Error deleting records: {e}")
        return 0


def insert_rows(client: Client, rows: list[dict]) -> tuple[int, int]:
    inserted = 0
    errors = 0
    for row in rows:
        try:
            client.table(TABLE_NAME).insert(row).execute()
            inserted += 1
        except Exception as e:
            print(f"  Error inserting student_id={row['student_id']}: {e}")
            errors += 1
    return inserted, errors


def check_student_exists(client: Client, student_id: str) -> bool:
    try:
        result = client.table(TABLE_NAME).select("student_id").eq("student_id", student_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking student_id={student_id}: {e}")
        return False


def main():
    if not STUDENTS_PATH.exists():
        print(f"Error: {STUDENTS_PATH} not found")
        sys.exit(1)

    client = get_client()
    rows = parse_students(STUDENTS_PATH)
    print(f"Parsed {len(rows)} student(s) from {STUDENTS_PATH}")
    delete_all(client)
    inserted, errors = insert_rows(client, rows)
    print(f"Inserted: {inserted}, Errors: {errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        if len(sys.argv) < 3:
            print("Usage: python src/supabase_classlist.py --check <student_id>")
            sys.exit(1)
        sid = sys.argv[2]
        client = get_client()
        exists = check_student_exists(client, sid)
        if exists:
            print(f"Student {sid} found in classlist")
            sys.exit(0)
        else:
            print(f"Student {sid} NOT found in classlist")
            sys.exit(1)
    else:
        main()
