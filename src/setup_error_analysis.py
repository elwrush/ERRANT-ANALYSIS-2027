#!/usr/bin/env python3
"""Create the error_analysis table and add error code columns to error_reports."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")

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


def execute_via_psycopg2():
    import psycopg2
    conn = psycopg2.connect(SUPABASE_DB_URL, sslmode="require")
    conn.autocommit = True
    cur = conn.cursor()
    for stmt in COLUMNS_SQL:
        cur.execute(stmt)
    cur.close()
    conn.close()
    print(f"Added {len(COLUMNS_SQL)} columns to error_reports")


def main():
    if not SUPABASE_DB_URL:
        print("Set SUPABASE_DB_URL in .env (get it from Supabase Dashboard → Project Settings → Database → Connection string, with password)")
        print("\nAlternatively, copy & paste the SQL below into the Supabase SQL editor:\n")
        for stmt in COLUMNS_SQL:
            print(stmt + ";")
        sys.exit(1)

    try:
        execute_via_psycopg2()
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\nMake sure SUPABASE_DB_URL is correct. Copy the connection string from:")
        print("  Supabase Dashboard → Project Settings → Database → Connection string (URI)")
        print("Then add it to .env as:")
        print('  SUPABASE_DB_URL="postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"')
        sys.exit(1)


if __name__ == "__main__":
    main()
