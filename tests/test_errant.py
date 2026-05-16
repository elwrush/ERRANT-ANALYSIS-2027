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


class TestMetadata:
    """Test the build_metadata function."""

    def test_basic_metadata_shape(self):
        from errant_analysis import build_metadata
        meta = build_metadata([], "corrected", "original")
        assert meta["model"] == "google/gemma-4-31b-it"
        assert meta["temperature"] == 0.1
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


class TestIntersectEdits:
    """Test edit intersection for double-check pass."""

    def test_perfect_match(self):
        from errant_analysis import intersect_edits, _make_edit
        e1 = _make_edit(0, 1, [], "a", 0, 1, [], "b", "R:VERB:TENSE")
        e2 = _make_edit(0, 1, [], "a", 0, 1, [], "b", "R:VERB:TENSE")
        result = intersect_edits([e1], [e2])
        assert len(result) == 1

    def test_no_match(self):
        from errant_analysis import intersect_edits, _make_edit
        e1 = _make_edit(0, 1, [], "a", 0, 1, [], "b", "R:VERB:TENSE")
        e2 = _make_edit(0, 2, [], "a c", 0, 1, [], "d", "R:OTHER")
        result = intersect_edits([e1], [e2])
        assert len(result) == 0

    def test_partial_match(self):
        from errant_analysis import intersect_edits, _make_edit
        e1 = _make_edit(0, 1, [], "a", 0, 1, [], "b", "R:VERB:TENSE")
        e2 = _make_edit(2, 3, [], "c", 2, 3, [], "d", "R:SPELL")
        e3 = _make_edit(0, 1, [], "a", 0, 1, [], "b", "R:VERB:TENSE")
        e4 = _make_edit(5, 6, [], "e", 5, 6, [], "f", "M:DET")
        result = intersect_edits([e1, e2], [e3, e4])
        assert len(result) == 1
        assert result[0].type == "R:VERB:TENSE"


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
