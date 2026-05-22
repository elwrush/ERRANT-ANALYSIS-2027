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
    # Clean stale files from previous test runs
    for f in TEST_DIR.iterdir():
        f.unlink()
    img = Image.new("RGB", (2000, 1500), "white")
    for name in ["img-0003.jpg", "img-0002.jpg", "img-0001.jpg"]:
        img.save(TEST_DIR / name, "JPEG", quality=95)


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
        url = preprocess_image(str(TEST_DIR / "img-0001.jpg"))
        assert url.startswith("data:image/jpeg;base64,")
        assert len(url) > 100

    def test_image_dimensions(self):
        url = preprocess_image(str(TEST_DIR / "img-0001.jpg"))
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
        assert len(groups) == 3
        for g in groups:
            assert len(g["pages"]) == 1

    def test_multi_page(self):
        groups = group_images(TEST_DIR, 2)
        assert len(groups) == 2
        assert len(groups[0]["pages"]) == 2
        assert len(groups[1]["pages"]) == 1

    def test_page_order(self):
        groups = group_images(TEST_DIR, 2)
        for g in groups:
            pages = g["pages"]
            names = [p.name for p in pages]
            assert names == sorted(names)

    def test_empty_folder(self, tmp_path):
        groups = group_images(tmp_path, 1)
        assert groups == []

    def test_no_matching_files(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hello")
        groups = group_images(tmp_path, 1)
        assert groups == []
