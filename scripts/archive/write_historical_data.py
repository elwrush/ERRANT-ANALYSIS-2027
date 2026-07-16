#!/usr/bin/env python3
"""Write historical test data for the 3 students. Falls back to local JSON if Supabase unavailable."""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HISTORICAL_DATA = {
    "29689": [
        {"student_id": "29689", "class": "M3-4A", "name": "Pun", "error_percent": 38, "date": "2026-02-10", "summary": "Pun has made steady progress this term, reducing errors from 38% to 30%. Keep working on articles and prepositions."},
        {"student_id": "29689", "class": "M3-4A", "name": "Pun", "error_percent": 35, "date": "2026-03-01", "summary": "Good improvement! Focus on subject-verb agreement and verb forms."},
        {"student_id": "29689", "class": "M3-4A", "name": "Pun", "error_percent": 30, "date": "2026-03-22", "summary": "Solid progress. Main errors are articles and prepositions — keep practicing!"},
    ],
    "29720": [
        {"student_id": "29720", "class": "M3-4A", "name": "Dragon", "error_percent": 18, "date": "2026-02-10", "summary": "Dragon writes clearly with good vocabulary. Focus on capitalization and word order."},
        {"student_id": "29720", "class": "M3-4A", "name": "Dragon", "error_percent": 15, "date": "2026-03-01", "summary": "Improving steadily. Watch out for missing punctuation at sentence ends."},
        {"student_id": "29720", "class": "M3-4A", "name": "Dragon", "error_percent": 14, "date": "2026-03-22", "summary": "Good progress. Main areas: spelling of proper nouns and verb form after suggest."},
    ],
    "35309": [
        {"student_id": "35309", "class": "M3-4A", "name": "Atom", "error_percent": 45, "date": "2026-02-10", "summary": "Atom has made significant improvement from 45% to 30%. Keep practicing SVA and spelling."},
        {"student_id": "35309", "class": "M3-4A", "name": "Atom", "error_percent": 38, "date": "2026-03-01", "summary": "Getting better! Focus on subject-verb agreement and article usage."},
        {"student_id": "35309", "class": "M3-4A", "name": "Atom", "error_percent": 30, "date": "2026-03-22", "summary": "Great improvement! Keep working on spelling and verb forms."},
    ],
}


def main():
    summary = ""
    for data in (x for items in HISTORICAL_DATA.values() for x in items):
        # Try Supabase first
        try:
            from supabase import create_client
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_ESL_KEY")
            if url and key:
                client = create_client(url, key)
                client.table("error_reports").insert(data).execute()
                summary += f"  Supabase: inserted {data['student_id']}: {data['error_percent']}%\n"
                continue
        except Exception:
            pass

        # Fallback: local JSON
        local_path = Path("local-working/historical_data.json")
        if local_path.exists():
            store = json.loads(local_path.read_text(encoding="utf-8"))
        else:
            store = []
        store.append(data)
        local_path.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
        summary += f"  Local: stored {data['student_id']}: {data['error_percent']}%\n"

    print(summary if summary else "No data written.")
    print("Done. 9 historical data points created (3 per student).")


if __name__ == "__main__":
    main()
