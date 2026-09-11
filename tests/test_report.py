import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)


class TestRenderReport:
    def test_report_template_renders(self):
        from jinja2 import Environment, FileSystemLoader
        template_path = Path(__file__).resolve().parent.parent / "templates" / "report.html"
        assert template_path.exists(), f"Template not found at {template_path}"

        env = Environment(loader=FileSystemLoader(str(template_path.parent)))
        tmpl = env.get_template(template_path.name)
        html = tmpl.render(
            student_id="99999", name="Test", class_label="M3-1A",
            word_count=100, error_rate=15, cefr_level="B2", target_rate=15,
            chart_path="/fake/path.png", summary_praise="", summary_errors=[],
            corrected_markup="Hello world.", original_text="Hello world.",
            today="July 13, 2026", header_logo_left="/images/ACT.png",
            header_logo_right="/images/cambridge.png",
        )
        assert "C·E·L Mathayom" in html
        assert "Writing Accuracy Feedback Report" in html
        assert "Test" in html
        assert "Hello world" in html
        assert "99999" in html
        assert "benchmark" in html.lower()
        assert "Your Writing with Corrections" in html
        assert "Your Original Writing (Uncorrected)" in html

    def test_esc_handles_special_chars(self):
        from generate_report import esc
        assert esc("#hello") == "\\#hello"
        assert esc("$5") == "\\$5"
        assert esc("[text]") == "\\[text\\]"


class TestChartGeneration:
    def test_generate_chart_creates_svg(self, tmp_path):
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
        assert Path(chart_path).suffix == ".svg"
        # Clean up
        Path(chart_path).unlink(missing_ok=True)

    def test_generate_chart_is_alpha_free(self):
        from generate_report import generate_chart
        import os
        os.chdir(Path(__file__).resolve().parent.parent)

        student = {"student_id": "99999", "error_rate": 20}
        data_points = [{"error_percent": 30, "created_at": "2026-01-15"}]
        chart_path = generate_chart(student, data_points)
        try:
            svg = Path(chart_path).read_text(encoding="utf-8")
            assert "opacity" not in svg
            assert "fill: #ffffff" in svg
        finally:
            Path(chart_path).unlink(missing_ok=True)


class TestHistoricalData:
    def test_fetch_historical_local_fallback(self):
        from generate_report import fetch_historical_data
        # Should return empty or local data without Supabase
        result = fetch_historical_data("99999")
        assert isinstance(result, list)


class TestTypstCompilation:
    def test_playwright_importable(self):
        import importlib
        try:
            importlib.import_module("playwright.sync_api")
        except ImportError:
            assert False, "playwright not installed"


class TestInferCefrLevel:
    def test_m3_is_b2(self):
        from generate_report import _infer_cefr_level
        assert _infer_cefr_level("M3-4A") == "B2"

    def test_m2_is_b1(self):
        from generate_report import _infer_cefr_level
        assert _infer_cefr_level("M2-4A") == "B1"

    def test_lower_class_is_b1(self):
        from generate_report import _infer_cefr_level
        assert _infer_cefr_level("M1-3A") == "B1"


class TestStripSalutation:
    def test_dear_name(self):
        from generate_report import _strip_salutation
        assert _strip_salutation("Dear John,\n\nHow are you?", "John") == "How are you?"

    def test_hi_name(self):
        from generate_report import _strip_salutation
        assert _strip_salutation("Hi Sarah,\n\nHello!", "Sarah") == "Hello!"

    def test_no_salutation(self):
        from generate_report import _strip_salutation
        assert _strip_salutation("Hello world.", "John") == "Hello world."


class TestHumanErrorType:
    def test_known(self):
        from generate_report import human_error_type
        assert "determiner" in human_error_type("R:DET").lower()
        assert "verb tense" in human_error_type("R:VERB:TENSE").lower()


class TestHtmlToPdfGraceful:
    def test_html_to_pdf_api(self):
        from generate_report import html_to_pdf
        assert callable(html_to_pdf)


class TestRenderReportMocked:
    def test_render_creates_pdf(self, mocker, tmp_path):
        mocker.patch("generate_report.html_to_pdf", return_value=tmp_path / "out.pdf")
        mocker.patch("generate_report._file_to_data_uri", return_value="data:image/svg+xml;base64,dGVzdA==")
        from generate_report import render_report
        student = {"student_id": "99999", "name": "T", "class": "M3-4A", "word_count": 10, "error_rate": 5}
        result = render_report(student, Path("templates/report.html"), tmp_path / "out.pdf")
        assert result is not None


class TestNoGhostscript:
    def test_report_modules_do_not_invoke_ghostscript(self):
        root = Path(__file__).resolve().parent.parent
        for name in ("generate_report.py", "technical_report_writer.py"):
            src = (root / "src" / name).read_text(encoding="utf-8")
            assert "pdfwrite" not in src, f"{name} still references pdfwrite"
            assert "subprocess" not in src, f"{name} still uses subprocess"
            assert '"gs"' not in src and "'gs'" not in src, f"{name} still invokes gs"


class TestSingleFileOutput:
    def test_main_writes_one_pdf_per_student(self, mocker, tmp_path):
        import json
        import generate_report as gr

        lw = tmp_path / "local-working"
        lw.mkdir()
        for sid in ("90001", "90002"):
            (lw / f"M2-3B-{sid}.json").write_text(
                json.dumps({
                    "student_id": sid, "class": "M2-3B", "name": sid,
                    "original_text": "x", "corrected_text": "x",
                    "word_count": 50, "error_rate": 10,
                }),
                encoding="utf-8",
            )

        pdf_dir = tmp_path / "PDF"
        mocker.patch.object(gr, "LOCAL_WORKING_DIR", lw)
        mocker.patch.object(gr, "PDF_DIR", pdf_dir)
        mocker.patch.object(gr, "OUTPUTS_DIR", tmp_path / "outputs")
        mocker.patch.object(gr, "fetch_historical_data", return_value=[])
        mocker.patch.object(gr, "generate_chart", return_value=None)

        def fake_render(student, template_path, output_path):
            Path(output_path).write_bytes(b"%PDF-1.4")
            return output_path

        mocker.patch.object(gr, "render_report", side_effect=fake_render)
        mocker.patch.object(sys, "argv", ["generate_report.py", "M2-3B"])

        gr.main()

        pdfs = sorted((pdf_dir / "M2-3B").glob("*.pdf"))
        assert len(pdfs) == 2
        assert not list((pdf_dir / "M2-3B").glob("*-errant-report*.pdf"))
        for p in pdfs:
            assert p.name.endswith(("-90001.pdf", "-90002.pdf"))
            assert re.match(r"^\d{2}-\d{2}-\d{2}-\d{4}-.+-9000[12]\.pdf$", p.name), p.name


