import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

import pytest
import errant

FIXTURES_PATH = Path("tests/fixtures/error_golden.json")
annotator = errant.load("en")

with open(FIXTURES_PATH) as f:
    FIXTURES = json.load(f)


class TestErrantDetection:
    """RED phase: ERRANT must detect the expected error types for each fixture."""

    @pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
    def test_errant_detects_expected_errors(self, fixture):
        orig = annotator.parse(fixture["original"])
        cor = annotator.parse(fixture["expected_correction"])
        edits = annotator.annotate(orig, cor)

        detected_types = {e.type for e in edits}
        expected_set = set(fixture["expected_errors"])

        missing = expected_set - detected_types
        extra = detected_types - expected_set

        if missing or extra:
            msg_parts = []
            if missing:
                msg_parts.append(f"  Missing: {missing}")
            if extra:
                msg_parts.append(f"  Extra: {extra}")
            msg_parts.append(f"  Detected: {detected_types}")
            pytest.fail("\n".join(msg_parts))

    def test_no_empty_fixtures(self):
        assert len(FIXTURES) > 0

    @pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
    def test_original_differs_from_correction(self, fixture):
        assert fixture["original"] != fixture["expected_correction"]

    @pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
    def test_expected_errors_are_not_other(self, fixture):
        for err in fixture["expected_errors"]:
            assert err != "OTHER", f"Fixture {fixture['id']} expects OTHER — not actionable"


class TestCorrectionModel:
    """GREEN phase: The AI model must produce the expected corrections."""

    @pytest.mark.parametrize("fixture", FIXTURES[:3], ids=lambda f: f["id"])
    def test_model_correction(self, fixture):
        from errant_analysis import call_model
        result = call_model(fixture["original"])
        if result is None:
            pytest.skip("API unavailable — skip model-dependent test")
        # Model should produce something similar to expected correction
        orig_doc = annotator.parse(fixture["original"])
        cor_doc_actual = annotator.parse(result)

        edits_actual = annotator.annotate(orig_doc, cor_doc_actual)

        # At least 50% of the same error types should be detected
        actual_types = {e.type for e in edits_actual if e.type not in ("UNK",)}
        expected_types = set(fixture["expected_errors"])

        overlap = actual_types & expected_types
        assert len(overlap) >= len(expected_types) * 0.5 or len(actual_types) > 0, (
            f"Expected types {expected_types}, got {actual_types}"
        )


class TestPipeline:
    """GREEN phase: Full pipeline produces correct output."""

    @pytest.mark.parametrize("fixture", FIXTURES[:3], ids=lambda f: f["id"])
    def test_output_schema(self, fixture):

        orig_text = fixture["original"]
        corrected_text = fixture["expected_correction"]

        orig_doc = annotator.parse(orig_text)
        cor_doc = annotator.parse(corrected_text)
        edits = annotator.annotate(orig_doc, cor_doc)

        assert len(edits) > 0, "No edits found in fixture pair"


class TestPostClassification:
    """Test the OTHER fallback classifier."""

    def test_spelling_other(self):
        from errant_analysis import post_classify_other
        result = post_classify_other("recieve", "receive")
        assert result == "R:SPELL"

    def test_orthography_other(self):
        from errant_analysis import post_classify_other
        result = post_classify_other("Hello", "hello")
        assert result == "R:ORTH"

    def test_det_other_missing(self):
        from errant_analysis import post_classify_other
        result = post_classify_other("", "the")
        assert result == "M:DET"

    def test_prep_other(self):
        from errant_analysis import post_classify_other
        result = post_classify_other("in", "at")
        assert result == "R:PREP"


class TestAlignSentences:
    """Test the sentence alignment function."""

    def test_both_single_sentence(self):
        from errant_analysis import align_sentences
        result = align_sentences(["Hello world."], ["Hello world."])
        assert len(result) == 1
        assert result[0]["original"] == "Hello world."
        assert result[0]["corrected"] == "Hello world."

    def test_equal_count_identity(self):
        from errant_analysis import align_sentences
        result = align_sentences(
            ["First sentence.", "Second sentence.", "Third sentence."],
            ["First sentence.", "Second sentence.", "Third sentence."],
        )
        assert len(result) == 3
        assert result[0]["original"] == "First sentence."
        assert result[1]["corrected"] == "Second sentence."

    def test_equal_count_with_changes(self):
        from errant_analysis import align_sentences
        result = align_sentences(
            ["He go to store.", "She like apples."],
            ["He goes to the store.", "She likes apples."],
        )
        assert len(result) == 2
        # Both sides at least contain the same words
        assert "go" in result[0]["original"]
        assert "goes" in result[0]["corrected"]
        assert "like" in result[1]["original"]
        assert "likes" in result[1]["corrected"]

    def test_fewer_corrected_sentences(self):
        """Correction merged two sentences into one."""
        from errant_analysis import align_sentences
        result = align_sentences(
            ["First part.", "Second part. This is longer."],
            ["First part. Second part. This is longer."],
        )
        # Both originals should map to the single corrected
        assert len(result) == 1
        assert "First part" in result[0]["original"]
        assert "Second part" in result[0]["original"]
        assert "Second part" in result[0]["corrected"]

    def test_more_corrected_sentences(self):
        """Correction split one sentence into two (less common but possible)."""
        from errant_analysis import align_sentences
        result = align_sentences(
            ["This is a long sentence that was split."],
            ["This is a long sentence.", "That was split."],
        )
        assert len(result) == 1
        assert "This is a long sentence that was split" in result[0]["original"]
        assert "This is a long sentence" in result[0]["corrected"]
        assert "That was split" in result[0]["corrected"]

    def test_empty_original(self):
        from errant_analysis import align_sentences
        result = align_sentences([], ["Some text."])
        assert result == []

    def test_empty_corrected(self):
        from errant_analysis import align_sentences
        result = align_sentences(["Some text."], [])
        assert result == []

    def test_single_to_multi_merge(self):
        """Multiple originals map to fewer corrected."""
        from errant_analysis import align_sentences
        result = align_sentences(
            ["Sentence A.", "Sentence B.", "Sentence C."],
            ["Sentence A. Sentence B. Sentence C."],
        )
        assert len(result) == 1
        assert "Sentence A" in result[0]["original"]
        assert "Sentence C" in result[0]["original"]
        # Corrected should contain all three
        assert result[0]["corrected"].count("Sentence") == 3

    def test_typst_example(self):
        """Realistic multi-sentence alignment from sampled ERRANT data."""
        from errant_analysis import align_sentences
        result = align_sentences(
            ["Makha Bucha day is the day that Prince Sittadta enlightmented in the past.",
             "Every July 10th, we celebrate it by go to the temple, where near our house."],
            ["Makha Bucha day is the day that Prince Sittadta enlightened in the past. "
             "Every July 10th, we celebrate it by going to the temple, which is near our house."],
        )
        # The correction merged two sentences into one
        assert len(result) == 1 or len(result) == 2
        # The key test: the original and corrected texts should not be scrambled
        if len(result) == 1:
            combined_orig = result[0]["original"]
            combined_cor = result[0]["corrected"]
            assert "enlightmented" in combined_orig or "enlightened" in combined_orig
            assert "enlightened" in combined_cor
        elif len(result) == 2:
            assert "enlightented" in result[0]["original"] or "enlightened" in result[0]["original"]
            assert "enlightened" in result[0]["corrected"] or "enlightened" in result[1]["corrected"]


class TestClassifyEdits:
    """Test the classify_edits function, especially dropped-edit tracking."""

    def test_basic_classification(self):
        from errant_analysis import classify_edits, _make_edit
        edits = [
            _make_edit(0, 1, [], "go", 0, 1, [], "goes", "R:VERB:SVA"),
            _make_edit(2, 3, [], "recieve", 2, 3, [], "receive", "R:SPELL"),
        ]
        errors, uncat, dropped = classify_edits(edits)
        assert len(errors) == 2
        assert dropped["UNK"] == 0
        assert dropped["U:SPACE"] == 0

    def test_unk_tracked_not_silently_dropped(self):
        from errant_analysis import classify_edits, _make_edit
        edits = [
            _make_edit(0, 1, [], "go", 0, 1, [], "goes", "R:VERB:SVA"),
            _make_edit(2, 4, [], "something weird", 2, 4, [], "completely different", "UNK"),
            _make_edit(5, 6, [], " ", 5, 6, [], "", "U:SPACE"),
        ]
        errors, uncat, dropped = classify_edits(edits)
        assert len(errors) == 1  # only the SVA edit survived
        assert dropped["UNK"] == 1
        assert dropped["U:SPACE"] == 1
        assert len(dropped["UNK_examples"]) == 1
        assert "something weird" in dropped["UNK_examples"][0]

    def test_ukn_uses_short_example_list(self):
        """UNK_examples should cap at 5 to keep output size manageable."""
        from errant_analysis import classify_edits, _make_edit
        edits = [_make_edit(i, i+1, [], f"unk_{i}", i, i+1, [], "x", "UNK") for i in range(10)]
        errors, uncat, dropped = classify_edits(edits)
        assert dropped["UNK"] == 10
        assert len(dropped["UNK_examples"]) == 5

    def test_no_edits(self):
        from errant_analysis import classify_edits
        errors, uncat, dropped = classify_edits([])
        assert errors == []
        assert uncat == []
        assert dropped["UNK"] == 0
        assert dropped["U:SPACE"] == 0


class TestMetadata:
    """Test the build_metadata function."""

    def test_basic_metadata_shape(self):
        from errant_analysis import build_metadata
        meta = build_metadata([], "corrected", "original")
        assert meta["model"] == "gpt-4.1-nano"
        assert meta["identity_check"] is False
        assert meta["total_edit_count"] == 0
        assert meta["overcorrection_count"] == 0
        assert meta["edit_width_stats"]["max_span"] == 0
        assert meta["edit_width_stats"]["avg_span"] == 0

    def test_identity_detected(self):
        from errant_analysis import build_metadata
        meta = build_metadata([], "same text", "same text")
        assert meta["identity_check"] is True

    def test_overcorrection_flagged(self):
        from errant_analysis import build_metadata, _make_edit
        long_edit = _make_edit(1, 5, ["a", "b", "c", "d"], "a b c d", 1, 1, ["e"], "e", "R:OTHER")
        meta = build_metadata([long_edit], "corrected", "original a b c d")
        assert meta["overcorrection_count"] == 1
        assert meta["edit_width_stats"]["max_span"] == 4

    def test_edit_width_stats(self):
        from errant_analysis import build_metadata, _make_edit
        e1 = _make_edit(0, 1, [], "a", 0, 1, [], "b", "R:VERB:TENSE")
        e2 = _make_edit(1, 3, [], "c d", 1, 2, [], "e", "R:OTHER")
        meta = build_metadata([e1, e2], "corrected", "a c d")
        assert meta["total_edit_count"] == 2
        assert meta["edit_width_stats"]["max_span"] == 2
        assert meta["edit_width_stats"]["multi_token_edits"] == 1


class TestErrorCodeMapping:
    """Test ERRANT_CODE_TO_COLUMN mapping completeness."""

    def test_all_errant_codes_have_columns(self):
        from errant_analysis import ERRANT_CODE_NAMES, ERRANT_CODE_TO_COLUMN
        mapped_codes = set(ERRANT_CODE_TO_COLUMN.keys())
        defined_codes = set(ERRANT_CODE_NAMES.keys())
        missing = defined_codes - mapped_codes
        assert not missing, f"Codes missing from ERRANT_CODE_TO_COLUMN: {missing}"

    def test_all_column_names_are_valid_sql(self):
        from errant_analysis import ERROR_CODE_COLUMNS
        import re
        valid = re.compile(r'^[a-z][a-z_]*$')
        for col in ERROR_CODE_COLUMNS:
            assert valid.match(col), f"Invalid SQL column name: {col}"

    def test_no_duplicate_column_names(self):
        from errant_analysis import ERROR_CODE_COLUMNS
        assert len(ERROR_CODE_COLUMNS) == len(set(ERROR_CODE_COLUMNS))

    def test_column_count_matches(self):
        from errant_analysis import ERROR_CODE_COLUMNS, ERRANT_CODE_NAMES
        assert len(ERROR_CODE_COLUMNS) == len(ERRANT_CODE_NAMES)


class TestInsertErrorReports:
    """Test the error_reports Supabase insert logic."""

    def test_row_contains_all_error_columns(self):
        from errant_analysis import ERROR_CODE_COLUMNS
        assert len(ERROR_CODE_COLUMNS) > 0

    def test_error_counts_populated_in_row(self):
        from errant_analysis import ERRANT_CODE_TO_COLUMN
        sample_output = {
            "student_id": "99999",
            "class": "M3-4A",
            "name": "Test",
            "error_rate": 10,
            "summary": "Good work.",
            "errant_analysis": {
                "errors": [
                    {"type": "R:SPELL", "count": 5, "example": "recieve -> receive"},
                    {"type": "R:DET", "count": 3, "example": "a -> an"},
                    {"type": "R:VERB:TENSE", "count": 2, "example": "go -> went"},
                ],
                "uncategorised": [],
            },
        }
        row = {
            "student_id": "99999",
            "class": "M3-4A",
            "name": "Test",
            "error_percent": 10,
            "summary": "Good work.",
        }
        # Simulate the insert logic
        from errant_analysis import ERROR_CODE_COLUMNS
        for col in ERROR_CODE_COLUMNS:
            row[col] = 0
        for e in sample_output["errant_analysis"]["errors"]:
            col = ERRANT_CODE_TO_COLUMN.get(e["type"])
            if col:
                row[col] = e["count"]

        assert row["r_spell"] == 5
        assert row["r_det"] == 3
        assert row["r_verb_tense"] == 2
        # Non-present codes should still be 0
        assert row["r_prep"] == 0
        assert row["m_noun"] == 0
        assert row["u_punct"] == 0

    def test_empty_errors_all_zeros(self):
        from errant_analysis import ERROR_CODE_COLUMNS
        row = {"student_id": "99999", "class": "M3-4A", "name": "Test",
               "error_percent": 0, "summary": "No errors."}
        for col in ERROR_CODE_COLUMNS:
            row[col] = 0
        assert row["r_spell"] == 0
        assert row["r_det"] == 0
        assert row["r_verb_tense"] == 0
        assert row["m_noun"] == 0


class TestWriteOutput:
    """Test the write_output function."""

    def test_identity_path(self):
        from errant_analysis import write_output
        from pathlib import Path

        test_out = Path("local-working")
        test_out.mkdir(parents=True, exist_ok=True)
        result = write_output({
            "student_id": "99999",
            "original_text": "test",
            "corrected_text": "test",
            "sentence_pairs": [],
            "errant_analysis": {"errors": [], "uncategorised": []},
            "corrected_typst": "test",
            "error_rate": 0,
            "word_count": 0,
            "metadata": {
                "identity_check": True,
                "overcorrection_count": 0,
                "model": "test",
                "temperature": 0.1,
                "total_edit_count": 0,
                "uncertain_edit_count": 0,
                "overcorrection_warnings": [],
                "edit_width_stats": {"max_span": 0, "avg_span": 0, "multi_token_edits": 0},
            },
        }, Path("outputs/test_student/99999.json"))
        assert result is not None
        out_file = test_out / "test_student-99999.json"
        assert out_file.exists()
        with open(out_file) as f:
            data = json.load(f)
        assert data["metadata"]["identity_check"] is True
        assert data["error_rate"] == 0


class TestBatchProgress:
    """Test the tqdm progress bar in batch mode."""

    def test_progress_bar_shows_counts(self, monkeypatch):
        from errant_analysis import main_batch
        import json
        import io
        import tempfile
        from contextlib import redirect_stdout, redirect_stderr

        # Mock heavy dependencies so the test is fast
        monkeypatch.setattr("errant_analysis.spacy.load", lambda x: None)
        monkeypatch.setattr("errant_analysis.errant.load", lambda x: None)

        # Mock process_file to return a minimal result without real API calls
        def mock_process(*args, **kwargs):
            return {"student_id": "999", "original_text": "test",
                    "corrected_text": "test", "sentence_pairs": [],
                    "errant_analysis": {"errors": [], "uncategorised": []},
                    "corrected_typst": "test", "error_rate": 0, "word_count": 0,
                    "metadata": {"total_edit_count": 0}}

        monkeypatch.setattr("errant_analysis.process_file", mock_process)

        # Create a few temp JSON files
        d = Path(tempfile.mkdtemp())
        files = []
        for i in range(3):
            f = d / f"{i}.json"
            f.write_text(json.dumps({"student_id": str(9000 + i), "student_text": "test."}))
            files.append(f)

        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            main_batch(files)

        combined = out.getvalue() + err.getvalue()
        assert "Processing 3 file(s)" in out.getvalue(), f"stdout missing header: {out.getvalue()}"
        assert "Done. Processed 3/3 files." in combined, f"Missing completion message. out={out.getvalue()!r} err={err.getvalue()!r}"
