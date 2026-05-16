#!/usr/bin/env python3
"""Query Supabase student_submissions table for count of skill=Writing."""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_ESL_KEY must be set in environment")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

result = client.table("student_submissions").select("*", count="exact").ilike("skill", "Writing").execute()

count = result.count if hasattr(result, "count") else len(result.data)
print(f"n for skill=Writing: {count}")
