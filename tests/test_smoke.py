"""Smoke tests: verify each module imports and has at least one callable function."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)



def _get_public_functions(module):
    return [n for n in dir(module) if callable(getattr(module, n)) and not n.startswith("_")]


class TestBatchErrantUpsert:
    def test_imports(self):
        import batch_errant_upsert
        assert hasattr(batch_errant_upsert, "process_one_record")


class TestMigrateWritingRecords:
    def test_imports(self):
        import migrate_writing_records
        funcs = _get_public_functions(migrate_writing_records)
        assert len(funcs) > 0


class TestRenameJsonFiles:
    def test_imports(self):
        import rename_json_files
        assert hasattr(rename_json_files, "extract_student_id")


class TestPreflightCheck:
    def test_imports(self):
        import preflight_check
        assert hasattr(preflight_check, "check_file")


class TestResearchPrep:
    def test_imports(self):
        os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
        os.environ.setdefault("SUPABASE_ESL_KEY", "test-key")
        import research_prep
        assert hasattr(research_prep, "clean_html")


class TestInterpretResults:
    def test_imports(self):
        import interpret_results
        assert hasattr(interpret_results, "extract_record")


class TestDeskStatistics:
    def test_imports(self):
        import desk_statistics
        assert hasattr(desk_statistics, "cliff_delta")


class TestSamplingStrategy:
    def test_module_compiles(self):
        import py_compile
        path = Path(__file__).resolve().parent.parent / "src" / "sampling_strategy.py"
        py_compile.compile(str(path), doraise=True)

    def test_has_valid_syntax(self):
        import ast
        path = Path(__file__).resolve().parent.parent / "src" / "sampling_strategy.py"
        ast.parse(path.read_text())


class TestSetupErrorAnalysis:
    def test_imports(self):
        import setup_error_analysis
        assert hasattr(setup_error_analysis, "execute_sql_via_utility")


class TestSupabaseSql:
    def test_imports(self):
        import supabase_sql
        assert hasattr(supabase_sql, "execute_via_api")
