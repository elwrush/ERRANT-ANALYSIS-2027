import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

from supabase_classlist import parse_students

STUDENTS_SAMPLE = """Class\tstudent_ID\t name
M2-4A\t36018\tPooh\t0
M2-5A\t30489\tMil\t0
M3-3A\t33266\tTaia\t0
"""


class TestParseStudents:
    def test_parses_valid_lines(self, tmp_path):
        f = tmp_path / "students.txt"
        f.write_text(STUDENTS_SAMPLE, encoding="utf-8")
        rows = parse_students(f)
        assert len(rows) == 3
        assert rows[0] == {"student_id": "36018", "name": "Pooh", "class": "M2-4A"}
        assert rows[1] == {"student_id": "30489", "name": "Mil", "class": "M2-5A"}
        assert rows[2] == {"student_id": "33266", "name": "Taia", "class": "M3-3A"}

    def test_skips_empty_student_id(self, tmp_path):
        content = "Class\tstudent_ID\t name\nM2-4A\t\tPooh\t0\nM2-4A\t36001\tPoch\t0\n"
        f = tmp_path / "students.txt"
        f.write_text(content, encoding="utf-8")
        rows = parse_students(f)
        assert len(rows) == 1
        assert rows[0]["student_id"] == "36001"

    def test_skips_short_lines(self, tmp_path):
        content = "Class\tstudent_ID\t name\nM2-4A\t36018\nM2-4A\t36001\tPoch\t0\n"
        f = tmp_path / "students.txt"
        f.write_text(content, encoding="utf-8")
        rows = parse_students(f)
        assert len(rows) == 1
        assert rows[0]["student_id"] == "36001"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "students.txt"
        f.write_text("Class\tstudent_ID\t name\n", encoding="utf-8")
        rows = parse_students(f)
        assert rows == []

    def test_ignores_trailing_column(self, tmp_path):
        f = tmp_path / "students.txt"
        f.write_text(STUDENTS_SAMPLE, encoding="utf-8")
        rows = parse_students(f)
        for r in rows:
            assert "0" not in r.values()

    def test_real_file_exists(self):
        path = Path("docs/students.txt")
        if path.exists():
            rows = parse_students(path)
            assert len(rows) > 0
            for r in rows:
                assert "student_id" in r
                assert r["student_id"].isdigit()


class TestDeleteAll:
    def test_delete_all_calls_delete(self, mocker):
        from supabase_classlist import delete_all
        mock_client = mocker.Mock()
        mock_client.table().delete().neq().execute.return_value = type("R", (), {"data": [{"student_id": "1"}, {"student_id": "2"}]})()
        result = delete_all(mock_client)
        assert result == 2

    def test_delete_all_error_returns_zero(self, mocker):
        from supabase_classlist import delete_all
        mock_client = mocker.Mock()
        mock_client.table().delete().neq().execute.side_effect = Exception("DB down")
        result = delete_all(mock_client)
        assert result == 0


class TestInsertRows:
    def test_insert_all_rows(self, mocker):
        from supabase_classlist import insert_rows
        mock_client = mocker.Mock()
        mock_client.table().insert().execute.return_value = type("R", (), {"data": [{"student_id": "36018"}]})()
        rows = [{"student_id": "36018", "name": "Pooh", "class": "M2-4A"}]
        inserted, errors = insert_rows(mock_client, rows)
        assert inserted == 1
        assert errors == 0

    def test_insert_error_counted(self, mocker):
        from supabase_classlist import insert_rows
        mock_client = mocker.Mock()
        mock_client.table().insert().execute.side_effect = Exception("DB down")
        rows = [{"student_id": "36018", "name": "Pooh", "class": "M2-4A"}]
        inserted, errors = insert_rows(mock_client, rows)
        assert inserted == 0
        assert errors == 1


class TestCheckStudentExists:
    def test_found(self, mocker):
        from supabase_classlist import check_student_exists
        mock_client = mocker.Mock()
        mock_client.table().select().eq().execute.return_value = type("R", (), {"data": [{"student_id": "36018"}]})()
        assert check_student_exists(mock_client, "36018") is True

    def test_not_found(self, mocker):
        from supabase_classlist import check_student_exists
        mock_client = mocker.Mock()
        mock_client.table().select().eq().execute.return_value = type("R", (), {"data": []})()
        assert check_student_exists(mock_client, "99999") is False

    def test_error_returns_false(self, mocker):
        from supabase_classlist import check_student_exists
        mock_client = mocker.Mock()
        mock_client.table().select().eq().execute.side_effect = Exception("DB down")
        assert check_student_exists(mock_client, "36018") is False
