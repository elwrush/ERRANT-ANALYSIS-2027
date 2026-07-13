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


class TestResponseFormat:
    def test_openrouter_payload_has_response_format(self, mocker):
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"student_id": "12345", "student_text": "hello"}'}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        from ingest import call_openrouter
        call_openrouter("data:image/jpeg;base64,aa")

        call_kwargs = mock_post.call_args_list[0][1] if mock_post.call_args_list else {}
        payload = call_kwargs.get("json", {})
        assert "response_format" in payload, "response_format not in payload"
        assert payload["response_format"] == {"type": "json_object"}, f"wrong response_format: {payload['response_format']}"


class TestIngestionOutputValidation:
    def test_rejects_non_5_digit_id(self):
        from models import IngestionOutput
        import pytest
        with pytest.raises(ValueError, match="student_id must be 5 digits"):
            IngestionOutput.model_validate({
                "student_id": "1234",
                "student_text": "hello",
                "word_count": 1,
            })

    def test_rejects_empty_text(self):
        from models import IngestionOutput
        import pytest
        with pytest.raises(ValueError, match="student_text must not be empty"):
            IngestionOutput.model_validate({
                "student_id": "12345",
                "student_text": "",
                "word_count": 1,
            })

    def test_accepts_valid_input(self):
        from models import IngestionOutput
        result = IngestionOutput.model_validate({
            "student_id": "12345",
            "student_text": "hello world",
            "word_count": 2,
        })
        assert result.student_id == "12345"
        assert result.word_count == 2


class TestHeuristicExtractName:
    def test_my_name_is(self):
        from ingest import heuristic_extract_name
        assert heuristic_extract_name("My name is John") == "John"

    def test_i_am(self):
        from ingest import heuristic_extract_name
        assert heuristic_extract_name("I am Sarah") == "Sarah"

    def test_no_match(self):
        from ingest import heuristic_extract_name
        assert heuristic_extract_name("Hello world") == ""

    def test_case_insensitive(self):
        from ingest import heuristic_extract_name
        assert heuristic_extract_name("MY NAME IS TOM") == "Tom"

    def test_short_name(self):
        from ingest import heuristic_extract_name
        assert heuristic_extract_name("I am A") == ""


class TestTryParseJson:
    def test_direct(self):
        from ingest import try_parse_json
        assert try_parse_json('{"a": 1}') == {"a": 1}

    def test_with_code_fence(self):
        from ingest import try_parse_json
        result = try_parse_json('```json\n{"a": 1}\n```')
        assert result == {"a": 1}

    def test_embedded(self):
        from ingest import try_parse_json
        result = try_parse_json('Text before {"a": 1} text after')
        assert result == {"a": 1}

    def test_malformed(self):
        from ingest import try_parse_json
        assert try_parse_json("not json") is None


class TestCallOpenrouterMocked:
    def test_returns_valid_json(self, mocker):
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"student_id": "12345", "student_text": "Hello"}'}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        from ingest import call_openrouter
        result = call_openrouter("data:image/jpeg;base64,aa")
        assert result is not None
        assert result["student_id"] == "12345"
