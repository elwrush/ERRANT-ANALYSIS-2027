#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")

LOCAL_WORKING_DIR = Path("local-working")
TABLE_NAME = "classlists"


def get_client() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def check_student_exists(client: Client, student_id: str) -> bool:
    try:
        result = client.table(TABLE_NAME).select("student_id").eq("student_id", student_id).execute()
        return len(result.data) > 0
    except Exception:
        return False


def find_json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.iterdir())


def extract_student_id(file_path: Path) -> str | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sid = data.get("student_id", "").strip()
        return sid if sid else None
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def main():
    client = get_client()

    files = find_json_files(LOCAL_WORKING_DIR)
    if not files:
        print(f"No JSON files found in {LOCAL_WORKING_DIR}/")
        sys.exit(0)

    renamed = 0
    skipped = []
    needs_supabase = []

    for f in files:
        if f.suffix != ".json":
            continue

        print(f"  Processing: {f.name}")
        sid = extract_student_id(f)

        if sid is None:
            print(f"    Skipped: no valid student_id in {f.name}")
            skipped.append(f.name)
            continue

        if client is None:
            needs_supabase.append((f, sid))
            print("    No Supabase credentials — will rename without validation")
            new_name = f"{sid}.json"
            new_path = f.parent / new_name
            if new_path.exists() and new_path != f:
                print(f"    Warning: {new_name} already exists, skipping")
                skipped.append(f.name)
            else:
                f.rename(new_path)
                print(f"    Renamed to: {new_name}")
                renamed += 1
            continue

        exists = check_student_exists(client, sid)
        if exists:
            new_name = f"{sid}.json"
            new_path = f.parent / new_name
            if new_path.exists() and new_path != f:
                print(f"    Warning: {new_name} already exists, skipping")
                skipped.append(f.name)
            else:
                f.rename(new_path)
                print(f"    Renamed to: {new_name}")
                renamed += 1
        else:
            print(f"    Skipped: student_id={sid} not found in classlist")
            skipped.append(f.name)

    print(f"\nRenamed: {renamed}")
    if skipped:
        print(f"Skipped ({len(skipped)}):")
        for s in skipped:
            print(f"  - {s}")
    sys.exit(0 if not skipped else 0)


if __name__ == "__main__":
    main()
