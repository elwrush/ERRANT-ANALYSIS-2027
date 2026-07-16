# Hallucinated Dependencies Audit: ERRANT-ANALYSIS

Scanned: Python imports, Lua requires, asset refs, subprocess cmds, URLs

## WARNINGS

- **`py-import`** in `src\batch_errant_upsert.py`: from `errant_analysis` import — module not found
- **`py-import`** in `src\errant_analysis.py`: from `_retry` import — module not found
- **`py-import`** in `src\errant_analysis.py`: from `generate_report` import — module not found
- **`py-import`** in `src\ingest.py`: from `_retry` import — module not found
- **`py-import`** in `src\setup_error_analysis.py`: from `supabase_sql` import — module not found
- **`py-import`** in `src\test_models.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_errant.py`: from `errant_analysis` import — module not found
- **`py-import`** in `tests\test_ingest.py`: from `ingest` import — module not found
- **`py-import`** in `tests\test_rename_json_files.py`: from `rename_json_files` import — module not found
- **`py-import`** in `tests\test_rename_json_files.py`: from `rename_json_files` import — module not found
- **`py-import`** in `tests\test_rename_json_files.py`: from `rename_json_files` import — module not found
- **`py-import`** in `tests\test_rename_json_files.py`: from `rename_json_files` import — module not found
- **`py-import`** in `tests\test_report.py`: from `generate_report` import — module not found
- **`py-import`** in `tests\test_report.py`: from `generate_report` import — module not found
- **`py-import`** in `tests\test_report.py`: from `generate_report` import — module not found
- **`py-import`** in `tests\test_report.py`: from `generate_report` import — module not found
- **`py-import`** in `tests\test_report.py`: from `generate_report` import — module not found
- **`py-import`** in `tests\test_report.py`: from `generate_report` import — module not found
- **`asset-html-src`** in `.kilo\node_modules\zod\README.md`: line 2: references `logo.svg` but file does not exist (resolved: C:\PROJECTS\ERRANT-ANALYSIS\.kilo\node_modules\zod\logo.svg)


---
**Summary:** 0 blockers, 50 warnings, 0 infos
