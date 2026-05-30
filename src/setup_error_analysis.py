#!/usr/bin/env python3
"""Add error code columns and date column to error_reports table.

Uses the supabase_sql utility (Management API or supabase CLI) — no psycopg2 needed.
Requires SUPABASE_ACCESS_TOKEN in environment or a linked project + supabase CLI.
"""
import os
import sys
from dotenv import load_dotenv
from supabase_sql import execute_via_api, execute_via_cli

load_dotenv()

NEW_COLUMNS = [
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS academic_year INTEGER DEFAULT 2007",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS date DATE",
]

COLUMNS_SQL = [
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_noun INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_noun_num INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_noun_poss INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_noun_infl INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_verb INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_verb_tense INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_verb_sva INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_verb_form INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_verb_infl INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_adj INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_adj_form INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_adv INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_prep INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_pron INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_det INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_conj INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_part INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_punct INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_spell INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_orth INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_morph INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_wo INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS r_contr INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_noun INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_noun_num INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_verb INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_verb_tense INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_verb_form INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_prep INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_pron INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_det INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_conj INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_part INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS m_punct INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_noun INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_verb INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_prep INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_pron INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_det INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_conj INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_part INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS u_punct INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS other INTEGER DEFAULT 0",
    "ALTER TABLE public.error_reports ADD COLUMN IF NOT EXISTS unk INTEGER DEFAULT 0",
]

BACKFILL_SQL = [
    "UPDATE public.error_reports SET date = created_at::date WHERE date IS NULL",
]


def execute_sql_via_utility(statements: list[str]):
    """Execute SQL statements using supabase CLI (preferred) or Management API (fallback)."""
    for stmt in statements:
        result = execute_via_cli(stmt)
        if result:
            # CLI succeeded; stmt was already executed
            if "UPDATE" in stmt.upper():
                print(f"  Executed: {stmt[:60]}...")
        else:
            # CLI not available — fall back to Management API
            execute_via_api(stmt)
            print(f"  Executed via API: {stmt[:60]}...")


def print_sql():
    """Print raw SQL statements for manual execution in Supabase dashboard."""
    print("-- Add new columns:")
    for stmt in NEW_COLUMNS + COLUMNS_SQL:
        print(stmt + ";")
    print("\n-- Backfill existing rows (run after column addition):")
    for stmt in BACKFILL_SQL:
        print(stmt + ";")


def main():
    if not os.environ.get("SUPABASE_ACCESS_TOKEN"):
        print("NOTE: SUPABASE_ACCESS_TOKEN not set.")
        print("  Generate one at: https://supabase.com/dashboard/account/tokens")
        print("  Then set:  $env:SUPABASE_ACCESS_TOKEN = 'sbp_...'")
        print()

    # Try CLI first, then API, then print SQL as last resort
    all_statements = NEW_COLUMNS + COLUMNS_SQL + BACKFILL_SQL

    has_cli = execute_via_cli("SELECT 1;")
    has_api = bool(os.environ.get("SUPABASE_ACCESS_TOKEN"))

    if has_cli or has_api:
        print("Running migration...")
        execute_sql_via_utility(all_statements)
        print(f"\nDone. Processed {len(all_statements)} SQL statement(s).")
    else:
        print("No supabase CLI available and SUPABASE_ACCESS_TOKEN not set.\n")
        print_sql()
        sys.exit(1)


if __name__ == "__main__":
    main()
