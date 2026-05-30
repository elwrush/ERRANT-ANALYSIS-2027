#!/usr/bin/env python3
"""Execute SQL on the linked Supabase project.

Two modes:
  1. Management API (default) — POST /v1/projects/{ref}/database/query → JSON output
  2. supabase CLI — `supabase db query --linked` (used only for DDL / execution)

Usage:
    python src/supabase_sql.py "SELECT COUNT(*) FROM error_reports"
    python src/supabase_sql.py -f path/to/migration.sql
    python src/supabase_sql.py --cli "SELECT * FROM error_reports LIMIT 3"  # force CLI mode

Requires (one of):
    SUPABASE_ACCESS_TOKEN — personal access token (generate at supabase.com/dashboard/account/tokens)
    supabase CLI installed and project linked:  supabase link --project-ref <ref>

Environment:
    SUPABASE_ACCESS_TOKEN    Personal Access Token for Management API
    SUPABASE_URL             API URL (e.g. https://xxxxx.supabase.co)
    SUPABASE_ESL_KEY         Service role key (for postgrest client, NOT for SQL execution)
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
import requests


def get_project_ref() -> str:
    """Read linked project ref from the local supabase/.temp directory."""
    candidates = [
        Path("supabase/.temp/project-ref"),
        Path("supabase/.temp/linked-project.json"),
    ]
    for p in candidates:
        if p.exists():
            raw = p.read_text(encoding="utf-8").strip()
            try:
                data = json.loads(raw)
                return data.get("ref", "")
            except json.JSONDecodeError:
                return raw
    print("Project not linked. Run:  supabase link --project-ref <ref>")
    sys.exit(1)


def cli_available() -> bool:
    """Check if the supabase CLI is installed and linked."""
    try:
        r = subprocess.run(
            ["supabase", "db", "query", "--linked", "SELECT 1;"],
            capture_output=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def execute_via_cli(sql: str) -> bool:
    """Execute SQL via `supabase db query --linked`. Returns True on success."""
    try:
        r = subprocess.run(
            ["supabase", "db", "query", "--linked", sql],
            capture_output=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def execute_via_api(sql: str) -> list[dict]:
    """Execute SQL via the Supabase Management API. Returns result rows."""
    token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if not token:
        print("Error: SUPABASE_ACCESS_TOKEN not set.")
        print("Generate one at: https://supabase.com/dashboard/account/tokens")
        print("Then:  $env:SUPABASE_ACCESS_TOKEN = 'sbp_...'")
        sys.exit(1)

    ref = get_project_ref()
    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"query": sql}

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    if r.status_code == 201:
        return r.json()
    else:
        print(f"API error {r.status_code}: {r.text[:500]}")
        sys.exit(1)


def _parse_sql(input_str: str) -> list[str]:
    """Split SQL input into individual statements, stripping comments."""
    statements = []
    for stmt in input_str.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        # Remove single-line comments
        lines = [line for line in stmt.split("\n")
                 if not line.strip().startswith("--")]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            statements.append(cleaned + ";")
    return statements


def _is_select(sql: str) -> bool:
    """Check if a SQL statement is a SELECT query (returns rows)."""
    stripped = sql.strip().upper()
    return stripped.startswith("SELECT") or stripped.startswith("WITH")


def main():
    parser = argparse.ArgumentParser(
        description="Execute SQL on the linked Supabase project",
        epilog="Examples:\n"
               "  python src/supabase_sql.py \"SELECT COUNT(*) FROM error_reports\"\n"
               "  python src/supabase_sql.py -f migrations/001_add_date.sql\n"
               "  python src/supabase_sql.py --api \"SELECT * FROM error_reports LIMIT 3\"",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("sql", nargs="?", help="SQL query string to execute")
    parser.add_argument("-f", "--file", help="Path to SQL file")
    parser.add_argument("--cli", action="store_true",
                        help="Force supabase CLI mode (table output with Unicode)")
    args = parser.parse_args()

    if args.file:
        sql = Path(args.file).read_text(encoding="utf-8")
    elif args.sql:
        sql = args.sql
    else:
        parser.print_help()
        sys.exit(1)

    statements = _parse_sql(sql)

    for stmt in statements:
        # CLI mode: use supabase CLI (Unicode table output)
        if args.cli:
            if execute_via_cli(stmt):
                continue
            else:
                print("CLI failed, falling back to API...")
                result = execute_via_api(stmt)
                if result:
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print("OK (no rows returned)")
            continue

        # Default: use API for queries (clean JSON), CLI for DDL
        if _is_select(stmt):
            result = execute_via_api(stmt)
            print(json.dumps(result, indent=2, default=str))
        else:
            if not execute_via_cli(stmt):
                # CLI not available — fall back to API
                execute_via_api(stmt)
                print("OK (executed via API)")


if __name__ == "__main__":
    main()
