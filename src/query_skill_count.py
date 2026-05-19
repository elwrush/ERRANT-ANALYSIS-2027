#!/usr/bin/env python3
"""Query writing_assessment_cambridge table and count records per assessment_type in batches."""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ESL_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_ESL_KEY must be set")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

result = client.table("writing_assessment_cambridge").select("*", count="exact").execute()

count = result.count if hasattr(result, "count") else len(result.data)
print(f"n for skill=Writing: {count}")
