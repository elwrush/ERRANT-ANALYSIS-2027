import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

from rename_json_files import extract_student_id, find_json_files


class TestExtractStudentId:
    def test_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"student_id": "36018", "name": "test"}))
        assert extract_student_id(f) == "36018"

    def test_missing_key(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"name": "test"}))
        assert extract_student_id(f) is None

    def test_empty_student_id(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"student_id": ""}))
        assert extract_student_id(f) is None

    def test_malformed_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text("not json")
        assert extract_student_id(f) is None

    def test_errant_format(self, tmp_path):
        f = tmp_path / "class-99999.json"
        f.write_text(json.dumps({
            "student_id": "99999",
            "original_text": "test",
            "corrected_text": "test",
            "sentence_pairs": [],
            "errant_analysis": {"errors": [], "uncategorised": []},
            "corrected_with_markup": "test",
            "error_rate": 0,
            "metadata": {},
        }))
        assert extract_student_id(f) == "99999"


class TestFindJsonFiles:
    def test_empty_directory(self, tmp_path):
        files = find_json_files(tmp_path)
        assert files == []

    def test_no_json(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hello")
        files = find_json_files(tmp_path)
        assert len(files) == 1

    def test_finds_json_files(self, tmp_path):
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        files = find_json_files(tmp_path)
        assert len(files) == 2
        assert all(f.suffix == ".json" for f in files)


class TestRenaming:
    def test_rename_valid_student(self, mocker, tmp_path):
        f = tmp_path / "class-36018.json"
        f.write_text(json.dumps({"student_id": "36018"}))

        mock_client = mocker.Mock()
        mock_client.table().select().eq().execute.return_value = type("R", (), {"data": [{"student_id": "36018"}]})()

        from rename_json_files import check_student_exists
        assert check_student_exists(mock_client, "36018") is True

    def test_rename_invalid_student(self, mocker, tmp_path):
        f = tmp_path / "class-99999.json"
        f.write_text(json.dumps({"student_id": "99999"}))

        mock_client = mocker.Mock()
        mock_client.table().select().eq().execute.return_value = type("R", (), {"data": []})()

        from rename_json_files import check_student_exists
        assert check_student_exists(mock_client, "99999") is False

    def test_supabase_error(self, mocker):
        from rename_json_files import check_student_exists
        mock_client = mocker.Mock()
        mock_client.table().select().eq().execute.side_effect = Exception("DB down")
        assert check_student_exists(mock_client, "36018") is False
