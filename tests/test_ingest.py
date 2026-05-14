import re
from pathlib import Path
from PIL import Image

import sys
import os
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

from ingest import preprocess_image, group_images, try_parse_json

TEST_DIR = Path("inputs/test_set")


def setup_module():
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (2000, 1500), "white")
    for name in ["12345_1.jpg", "12345_2.jpg", "67890_1.jpg"]:
        img.save(TEST_DIR / name, "JPEG", quality=95)


class TestFilenameGrouping:
    pattern = re.compile(r"^(\d+)_(\d+)")

    def test_standard_name(self):
        m = self.pattern.match("12345_1")
        assert m is not None
        assert m.groups() == ("12345", "1")

    def test_multi_digit_id(self):
        m = self.pattern.match("98765_12")
        assert m is not None
        assert m.groups() == ("98765", "12")

    def test_leading_zeros(self):
        m = self.pattern.match("00123_1")
        assert m is not None
        assert m.groups() == ("00123", "1")

    def test_non_matching(self):
        assert self.pattern.match("foo_bar") is None
        assert self.pattern.match("notes") is None
        assert self.pattern.match("12345.jpg") is None


class TestJsonParsing:
    def test_direct_json(self):
        result = try_parse_json('{"student_id": "12345", "student_text": "hello world"}')
        assert result == {"student_id": "12345", "student_text": "hello world"}

    def test_fenced_json(self):
        raw = "```json\n{\"student_id\": \"12345\", \"student_text\": \"hello\"}\n```"
        result = try_parse_json(raw)
        assert result == {"student_id": "12345", "student_text": "hello"}

    def test_embedded_json(self):
        raw = "Here is the result: {\"student_id\": \"12345\", \"student_text\": \"hello\"}"
        result = try_parse_json(raw)
        assert result == {"student_id": "12345", "student_text": "hello"}

    def test_malformed_no_braces(self):
        result = try_parse_json("This is just plain text with no JSON")
        assert result is None

    def test_incomplete_json(self):
        result = try_parse_json('{"student_id": "12345"')
        assert result is None


class TestPreprocessing:
    def test_data_url_format(self):
        url = preprocess_image(str(TEST_DIR / "12345_1.jpg"))
        assert url.startswith("data:image/jpeg;base64,")
        assert len(url) > 100

    def test_image_dimensions(self):
        url = preprocess_image(str(TEST_DIR / "12345_1.jpg"))
        b64 = url.split(",", 1)[1]
        import base64
        import io
        img = Image.open(io.BytesIO(base64.b64decode(b64)))
        w, h = img.size
        assert w <= 1024
        assert h <= 1024
        assert img.mode == "L"

    def test_nonexistent_file(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            preprocess_image("nonexistent.jpg")


class TestGrouping:
    def test_single_page(self):
        groups = group_images(TEST_DIR, 1)
        assert len(groups) == 2
        ids = [g["student_id"] for g in groups]
        assert "12345" in ids
        assert "67890" in ids

    def test_multi_page(self):
        groups = group_images(TEST_DIR, 2)
        assert len(groups) == 2
        for g in groups:
            if g["student_id"] == "12345":
                assert len(g["pages"]) == 2
            elif g["student_id"] == "67890":
                assert len(g["pages"]) == 1

    def test_page_order(self):
        groups = group_images(TEST_DIR, 2)
        for g in groups:
            pages = g["pages"]
            page_nums = [int(p.stem.split("_")[1]) for p in pages]
            assert page_nums == sorted(page_nums)

    def test_empty_folder(self, tmp_path):
        groups = group_images(tmp_path, 1)
        assert groups == []

    def test_no_matching_files(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hello")
        groups = group_images(tmp_path, 1)
        assert groups == []
