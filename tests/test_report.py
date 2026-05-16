import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)


class TestTypContent:
    def test_build_student_block_produces_valid_string(self):
        from generate_report import build_student_block
        sample = {
            "student_id": "99999",
            "name": "Test",
            "class": "M3-1A",
            "error_rate": 15,
            "summary": "Dear Test, good writing!",
            "original_text": "Hello world.",
            "corrected_text": "Hello world.",
            "corrected_with_markup": "Hello world.",
            "errant_analysis": {"errors": [
                {"type": "R:SPELL", "count": 2, "example": "hello -> hello"},
            ]},
        }
        result = build_student_block(sample, 0)
        assert isinstance(result, str)
        assert len(result) > 100
        assert "Test - 99999 - M3-1A" in result
        assert "Test" in result
        assert "Hello world" in result
        assert "Your Writing with Corrections" in result
        assert "We scanned your writing for errors and underlined the corrections" in result
        assert "target error rate" in result.lower()
        assert "Writing Accuracy Feedback Report" in result
        assert "*Dear Test,*" in result
        assert 'pad-anchor-0' in result
        assert 'pagebreak()' in result

    def test_header_is_valid(self):
        from generate_report import build_typ_header
        result = build_typ_header()
        assert isinstance(result, str)
        assert "Roboto" in result
        assert "14pt" in result
        assert "Mathayom Program" in result
        assert "place(top + left, dy: 0cm)[" in result

    def test_esc_handles_special_chars(self):
        from generate_report import esc
        assert esc("#hello") == "\\#hello"
        assert esc("$5") == "\\$5"
        assert esc("[text]") == "\\[text\\]"

    def test_convert_markup_handles_u_tags(self):
        from generate_report import convert_markup
        result = convert_markup("Hello <u>world</u>.")
        assert "#underline[" in result
        assert "world" in result


class TestChartGeneration:
    def test_generate_chart_creates_png(self, tmp_path):
        from generate_report import generate_chart
        import os
        os.chdir(Path(__file__).resolve().parent.parent)

        student = {"student_id": "99999", "error_rate": 20}
        data_points = [
            {"error_percent": 35, "created_at": "2026-01-15"},
            {"error_percent": 25, "created_at": "2026-02-20"},
        ]
        chart_path = generate_chart(student, data_points)
        assert Path(chart_path).exists()
        assert Path(chart_path).suffix == ".png"
        # Clean up
        Path(chart_path).unlink(missing_ok=True)


class TestHistoricalData:
    def test_fetch_historical_local_fallback(self):
        from generate_report import fetch_historical_data
        # Should return empty or local data without Supabase
        result = fetch_historical_data("99999")
        assert isinstance(result, list)


class TestTypstCompilation:
    def test_typst_installed(self):
        import subprocess
        result = subprocess.run(["typst", "--version"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "typst" in result.stdout.lower()
