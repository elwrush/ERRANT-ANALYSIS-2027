import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

import pytest


class TestIngestionOutput:
    def test_valid(self):
        from models import IngestionOutput
        r = IngestionOutput.model_validate({
            "student_id": "12345",
            "student_text": "Hello world.",
            "word_count": 2,
        })
        assert r.student_id == "12345"

    def test_invalid_id_short(self):
        from models import IngestionOutput
        with pytest.raises(ValueError, match="student_id must be 5 digits"):
            IngestionOutput.model_validate({
                "student_id": "1234",
                "student_text": "Hi",
                "word_count": 1,
            })

    def test_invalid_id_empty(self):
        from models import IngestionOutput
        with pytest.raises(ValueError, match="student_id must be 5 digits"):
            IngestionOutput.model_validate({
                "student_id": "",
                "student_text": "Hi",
                "word_count": 1,
            })

    def test_invalid_id_non_digit(self):
        from models import IngestionOutput
        with pytest.raises(ValueError, match="student_id must be 5 digits"):
            IngestionOutput.model_validate({
                "student_id": "abcde",
                "student_text": "Hi",
                "word_count": 1,
            })

    def test_empty_text(self):
        from models import IngestionOutput
        with pytest.raises(ValueError, match="student_text must not be empty"):
            IngestionOutput.model_validate({
                "student_id": "12345",
                "student_text": "",
                "word_count": 1,
            })

    def test_zero_word_count(self):
        from models import IngestionOutput
        with pytest.raises(ValueError, match="word_count must be >= 1"):
            IngestionOutput.model_validate({
                "student_id": "12345",
                "student_text": "Hi",
                "word_count": 0,
            })

    def test_class_alias(self):
        from models import IngestionOutput
        r = IngestionOutput.model_validate({
            "student_id": "12345",
            "student_text": "Hi",
            "word_count": 1,
            "class": "M3-4A",
        })
        assert r.class_ == "M3-4A"


class TestErrantOutput:
    def test_valid_minimal(self):
        from models import ErrantOutput
        r = ErrantOutput.model_validate({
            "student_id": "12345",
            "original_text": "He go to store.",
            "corrected_text": "He goes to the store.",
            "word_count": 4,
            "date_created": "2026-07-13",
        })
        assert r.student_id == "12345"

    def test_valid_with_class_alias(self):
        from models import ErrantOutput
        r = ErrantOutput.model_validate({
            "student_id": "12345",
            "original_text": "He go.",
            "corrected_text": "He goes.",
            "word_count": 2,
            "date_created": "2026-07-13",
            "class": "M2",
        })
        assert r.class_ == "M2"

    def test_error_rate_out_of_range(self):
        from models import ErrantOutput
        with pytest.raises(ValueError):
            ErrantOutput.model_validate({
                "student_id": "12345",
                "original_text": "test",
                "corrected_text": "test",
                "error_rate": 101,
                "date_created": "2026-07-13",
            })

    def test_empty_original_text(self):
        from models import ErrantOutput
        with pytest.raises(ValueError, match="original_text must not be empty"):
            ErrantOutput.model_validate({
                "student_id": "12345",
                "original_text": "",
                "corrected_text": "test",
                "word_count": 1,
                "date_created": "2026-07-13",
            })

    def test_empty_corrected_text(self):
        from models import ErrantOutput
        with pytest.raises(ValueError, match="corrected_text must not be empty"):
            ErrantOutput.model_validate({
                "student_id": "12345",
                "original_text": "test",
                "corrected_text": "",
                "word_count": 1,
                "date_created": "2026-07-13",
            })


class TestReportData:
    def test_valid(self):
        from models import ReportData
        r = ReportData.model_validate({
            "student_id": "12345",
            "name": "Test",
            "class": "M3-4A",
            "word_count": 100,
        })
        assert r.student_id == "12345"
        assert r.cefr_level == "B2"
        assert r.target_rate == 7

    def test_invalid_id(self):
        from models import ReportData
        with pytest.raises(ValueError):
            ReportData.model_validate({
                "student_id": "abcd",
                "name": "Test",
                "class": "M3-4A",
                "word_count": 100,
            })
