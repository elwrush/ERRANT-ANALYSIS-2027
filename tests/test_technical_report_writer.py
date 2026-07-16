import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

import pytest


def _valid_errant_dict():
    return {
        "student_id": "12345",
        "original_text": "I goes to school.",
        "corrected_text": "I go to school.",
        "sentence_pairs": [],
        "corrected_typst": "",
        "error_rate": 10,
        "word_count": 4,
        "name": "Test",
        "class": "M2A",
        "record_id": "",
        "submission_date": "2026-01-15",
        "topic": "",
        "summary": "",
        "summary_data": None,
        "summary_type": "",
        "date_created": "2026-01-15",
        "metadata": {"model": "deepseek-v4-flash"},
        "errant_analysis": {
            "errors": [],
            "uncategorised": [],
            "dropped_edits": {},
        },
    }


class TestPydanticModels:
    def test_validation_result_valid(self):
        from technical_report_writer import ValidationResult
        r = ValidationResult.model_validate({
            "valid_files": ["/tmp/a.json"],
            "invalid_files": [],
            "total_checked": 1,
        })
        assert r.total_checked == 1
        assert len(r.valid_files) == 1
        assert len(r.invalid_files) == 0

    def test_validation_result_with_invalid(self):
        from technical_report_writer import ValidationResult
        r = ValidationResult.model_validate({
            "valid_files": [],
            "invalid_files": [{
                "path": "/tmp/bad.json",
                "errors": [{"field": "student_id", "message": "must be 5 digits"}],
            }],
            "total_checked": 1,
        })
        assert r.total_checked == 1
        assert r.invalid_files[0].path == Path("/tmp/bad.json")
        assert r.invalid_files[0].errors[0].field == "student_id"

    def test_report_meta(self):
        from technical_report_writer import ReportMeta
        m = ReportMeta.model_validate({
            "title": "Test Report",
            "generated_at": "2026-07-14T10:00:00",
            "n_students": 30,
            "n_classes": 2,
            "cohorts": ["M2", "M3"],
            "date_range": ("2026-01-01", "2026-06-30"),
        })
        assert m.title == "Test Report"
        assert m.n_students == 30

    def test_student_summary(self):
        from technical_report_writer import StudentSummary
        s = StudentSummary.model_validate({
            "student_id": "12345",
            "name": "Test Student",
            "class_": "M2A",
            "word_count": 120,
            "error_rate": 15,
            "cefr_level": "B1",
            "error_count": 18,
            "top_errors": [],
        })
        assert s.student_id == "12345"
        assert s.error_rate == 15

    def test_student_summary_invalid_id(self):
        from technical_report_writer import StudentSummary
        with pytest.raises(ValueError, match="student_id must be 5 digits"):
            StudentSummary.model_validate({
                "student_id": "1234",
                "name": "Bad",
                "class_": "M2A",
                "word_count": 50,
                "error_rate": 10,
                "cefr_level": "B1",
                "error_count": 5,
                "top_errors": [],
            })

    def test_error_code_bucket(self):
        from technical_report_writer import ErrorCodeBucket
        b = ErrorCodeBucket.model_validate({
            "code": "R:VERB:TENSE",
            "supercategory": "R",
            "name": "Problems with verb tense",
            "count": 42,
            "percentage": 35.0,
        })
        assert b.count == 42
        assert b.percentage == 35.0

    def test_cohort_bucket(self):
        from technical_report_writer import CohortBucket
        c = CohortBucket.model_validate({
            "cohort": "M2",
            "n_students": 15,
            "mean_error_rate": 12.5,
            "median_error_rate": 11.0,
            "std_error_rate": 4.2,
            "min_error_rate": 5.0,
            "max_error_rate": 22.0,
        })
        assert c.cohort == "M2"
        assert c.mean_error_rate == 12.5

    def test_overall_stats(self):
        from technical_report_writer import OverallStats
        o = OverallStats.model_validate({
            "n_students": 30,
            "mean_error_rate": 10.5,
            "median_error_rate": 9.0,
            "std_error_rate": 5.1,
            "min_error_rate": 2.0,
            "max_error_rate": 25.0,
            "mean_word_count": 150.0,
            "b1_count": 18,
            "b2_count": 12,
        })
        assert o.n_students == 30
        assert o.b1_count == 18

    def test_chart_ref(self):
        from technical_report_writer import ChartRef
        cr = ChartRef.model_validate({
            "section": "introduction",
            "path": "/tmp/chart.png",
            "caption": "Error frequency by category",
            "type": "bar",
        })
        assert cr.type == "bar"

    def test_reference_entry(self):
        from technical_report_writer import ReferenceEntry
        ref = ReferenceEntry.model_validate({
            "authors": "Ellis, R.",
            "year": "2008",
            "title": "The Study of Second Language Acquisition",
            "source": "Oxford University Press",
            "doi": "https://doi.org/10.xxxx",
        })
        assert ref.authors == "Ellis, R."
        assert ref.doi == "https://doi.org/10.xxxx"

    def test_tech_report_template_context(self):
        from technical_report_writer import TechReportTemplateContext
        ctx = TechReportTemplateContext.model_validate({
            "masthead_left": "/images/ACT.png",
            "masthead_center": "C·E·L Mathayom",
            "masthead_right": "/images/cambridge.png",
            "report_title": "Test Report",
            "generated_at": "July 14, 2026",
            "sections": [{
                "id": "introduction",
                "title": "Introduction",
                "rhetorical_question": None,
                "body": "<p>Test</p>",
                "charts": [],
                "tables": [],
                "is_baseline": True,
            }],
            "references": [],
            "appendix_tables": [],
        })
        assert len(ctx.sections) == 1
        assert ctx.sections[0].id == "introduction"

    def test_aggregated_report_data(self):
        from technical_report_writer import (
            AggregatedReportData,
        )
        data = AggregatedReportData.model_validate({
            "meta": {
                "title": "Test",
                "generated_at": "2026-07-14T10:00:00",
                "n_students": 1,
                "n_classes": 1,
                "cohorts": ["M2"],
                "date_range": ("2026-01-01", "2026-06-30"),
            },
            "students": [{
                "student_id": "12345",
                "name": "Test",
                "class_": "M2A",
                "word_count": 100,
                "error_rate": 10,
                "cefr_level": "B1",
                "error_count": 10,
                "top_errors": [],
            }],
            "error_code_summary": [],
            "cohort_summary": [],
            "overall_stats": {
                "n_students": 1,
                "mean_error_rate": 10.0,
                "median_error_rate": 10.0,
                "std_error_rate": 0.0,
                "min_error_rate": 10.0,
                "max_error_rate": 10.0,
                "mean_word_count": 100.0,
                "b1_count": 1,
                "b2_count": 0,
            },
            "charts": [],
        })
        assert data.meta.n_students == 1
        assert len(data.students) == 1

    def test_citation_span(self):
        from technical_report_writer import CitationSpan
        cs = CitationSpan.model_validate({
            "source_path": "/tmp/source.pdf",
            "page": 42,
            "text": "Explicit instruction leads to improvement",
            "section": "Introduction",
            "citation_text": "(Ellis, 2008, p. 42)",
        })
        assert cs.page == 42
        assert cs.section == "Introduction"

    def test_citation_map_entry(self):
        from technical_report_writer import CitationMapEntry
        cm = CitationMapEntry.model_validate({
            "citation_text": "(Ellis, 2008, p. 42)",
            "source_file": "Ellis-2008-annotated.pdf",
            "page": 42,
            "quoted_passage": "Explicit instruction leads to improvement",
        })
        assert cm.source_file == "Ellis-2008-annotated.pdf"


class TestValidateInputFiles:
    def test_valid_single_file(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            data = _valid_errant_dict()
            (path / "test.json").write_text(json.dumps(data), encoding="utf-8")
            result = validate_input_files(path)
            assert result.total_checked == 1
            assert len(result.valid_files) == 1
            assert len(result.invalid_files) == 0

    def test_multiple_valid_files(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            for i in range(3):
                d = _valid_errant_dict()
                d["student_id"] = f"1234{i}"
                (path / f"stu{i}.json").write_text(json.dumps(d), encoding="utf-8")
            result = validate_input_files(path)
            assert result.total_checked == 3
            assert len(result.valid_files) == 3

    def test_invalid_field_value(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            d = _valid_errant_dict()
            d["original_text"] = ""
            (path / "bad.json").write_text(json.dumps(d), encoding="utf-8")
            result = validate_input_files(path)
            assert result.total_checked == 1
            assert len(result.invalid_files) == 1
            assert any("original_text" in e.field for e in result.invalid_files[0].errors)

    def test_missing_required_field(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            d = _valid_errant_dict()
            del d["student_id"]
            (path / "bad.json").write_text(json.dumps(d), encoding="utf-8")
            result = validate_input_files(path)
            assert result.total_checked == 1
            assert len(result.invalid_files) == 1

    def test_skips_non_json_files(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            d = _valid_errant_dict()
            (path / "data.json").write_text(json.dumps(d), encoding="utf-8")
            (path / "notes.txt").write_text("hello", encoding="utf-8")
            result = validate_input_files(path)
            assert result.total_checked == 1
            assert len(result.valid_files) == 1

    def test_empty_directory_raises(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            with pytest.raises(ValueError, match="No JSON files found at"):
                validate_input_files(path)

    def test_nonexistent_path_raises(self):
        from technical_report_writer import validate_input_files
        with pytest.raises(FileNotFoundError):
            validate_input_files(Path("/tmp/does_not_exist_xyz789"))

    def test_empty_directory_message(self):
        from technical_report_writer import validate_input_files
        with tempfile.TemporaryDirectory() as tmp, pytest.raises(ValueError, match="No JSON files found at"):
            validate_input_files(Path(tmp))


class TestAggregateData:
    def _write_json(self, path: Path, student_id: str, class_: str, error_rate: int | None, errors: list[dict]):
        d = _valid_errant_dict()
        d["student_id"] = student_id
        d["class"] = class_
        d["error_rate"] = error_rate
        d["errant_analysis"]["errors"] = errors
        (path / f"{student_id}.json").write_text(json.dumps(d), encoding="utf-8")

    def test_single_student(self):
        from technical_report_writer import aggregate_data, validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._write_json(p, "12345", "M2A", 10, [{"error_code": "R:VERB:TENSE"}])
            vr = validate_input_files(p)
            result = aggregate_data(vr.valid_files)
            assert result.meta.n_students == 1
            assert len(result.students) == 1
            assert result.students[0].student_id == "12345"
            assert result.overall_stats.mean_error_rate == 10.0

    def test_multiple_students(self):
        from technical_report_writer import aggregate_data, validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._write_json(p, "12345", "M2A", 10, [])
            self._write_json(p, "12346", "M2B", 15, [])
            self._write_json(p, "12347", "M3A", 5, [])
            vr = validate_input_files(p)
            result = aggregate_data(vr.valid_files)
            assert result.meta.n_students == 3
            assert result.meta.n_classes == 3
            assert set(result.meta.cohorts) == {"M2", "M3"}
            assert result.overall_stats.mean_error_rate == 10.0

    def test_multiple_cohorts(self):
        from technical_report_writer import aggregate_data, validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._write_json(p, "12345", "M2A", 10, [])
            self._write_json(p, "12346", "M3A", 5, [])
            vr = validate_input_files(p)
            result = aggregate_data(vr.valid_files)
            assert len(result.cohort_summary) == 2
            m2 = [c for c in result.cohort_summary if c.cohort == "M2"][0]
            assert m2.n_students == 1
            assert m2.mean_error_rate == 10.0

    def test_no_errors(self):
        from technical_report_writer import aggregate_data, validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._write_json(p, "12345", "M2A", 0, [])
            vr = validate_input_files(p)
            result = aggregate_data(vr.valid_files)
            assert result.overall_stats.mean_error_rate == 0.0
            assert len(result.error_code_summary) == 0

    def test_mixed_cefr_levels(self):
        from technical_report_writer import aggregate_data, validate_input_files
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._write_json(p, "12345", "M2A", 10, [])  # B1
            self._write_json(p, "12346", "M3A", 5, [])  # B2
            vr = validate_input_files(p)
            result = aggregate_data(vr.valid_files)
            assert result.overall_stats.b1_count == 1
            assert result.overall_stats.b2_count == 1

    def test_empty_valid_files_raises(self):
        from technical_report_writer import aggregate_data
        with pytest.raises(ValueError, match="No valid files"):
            aggregate_data([])


def _sample_aggregated_data():
    from technical_report_writer import (
        AggregatedReportData, ReportMeta, StudentSummary,
        OverallStats, CohortBucket, ErrorCodeBucket,
    )
    return AggregatedReportData(
        meta=ReportMeta(
            title="Test", generated_at="2026-07-14T10:00:00",
            n_students=30, n_classes=3, cohorts=["M2", "M3", "M4"],
            date_range=("2026-01-01", "2026-06-30"),
        ),
        students=[
            StudentSummary(student_id="12345", name="S1", class_="M2A", word_count=100, error_rate=10, cefr_level="B1", error_count=5, top_errors=[]),
            StudentSummary(student_id="12346", name="S2", class_="M3A", word_count=120, error_rate=8, cefr_level="B2", error_count=3, top_errors=[]),
        ],
        error_code_summary=[
            ErrorCodeBucket(code="R:VERB:TENSE", supercategory="R", name="Verb tense", count=20, percentage=40.0),
            ErrorCodeBucket(code="M:DET", supercategory="M", name="Missing determiner", count=15, percentage=30.0),
        ],
        cohort_summary=[
            CohortBucket(cohort="M2", n_students=15, mean_error_rate=12.0, median_error_rate=11.0, std_error_rate=4.0, min_error_rate=5.0, max_error_rate=22.0),
            CohortBucket(cohort="M3", n_students=10, mean_error_rate=8.0, median_error_rate=7.5, std_error_rate=3.0, min_error_rate=3.0, max_error_rate=15.0),
        ],
        overall_stats=OverallStats(
            n_students=30, mean_error_rate=10.0, median_error_rate=9.0, std_error_rate=5.0,
            min_error_rate=2.0, max_error_rate=25.0, mean_word_count=150.0, b1_count=18, b2_count=12,
        ),
        charts=[],
    )


class TestGenerateCharts:
    def test_chart_files_created(self):
        from technical_report_writer import generate_charts
        data = _sample_aggregated_data()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            refs = generate_charts(data, out)
            assert len(refs) >= 2
            for r in refs:
                assert r.path.exists(), f"Chart not found: {r.path}"

    def test_single_cohort_skip_comparison(self):
        from technical_report_writer import generate_charts, CohortBucket
        data = _sample_aggregated_data()
        data.cohort_summary = [
            CohortBucket(cohort="M2", n_students=30, mean_error_rate=10.0, median_error_rate=9.0, std_error_rate=5.0, min_error_rate=2.0, max_error_rate=25.0),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            refs = generate_charts(data, out)
            types = [r.type for r in refs]
            assert "grouped_bar" not in types

    def test_few_students_no_histogram(self):
        from technical_report_writer import generate_charts
        data = _sample_aggregated_data()
        data.overall_stats.n_students = 3
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            refs = generate_charts(data, out)
            types = [r.type for r in refs]
            assert "histogram" not in types

    def test_charts_grayscale(self):
        from technical_report_writer import generate_charts
        from PIL import Image
        import numpy as np
        data = _sample_aggregated_data()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            refs = generate_charts(data, out)
            for r in refs:
                img = Image.open(r.path).convert("RGB")
                arr = np.array(img)
                if arr.size > 0:
                    r_eq_g = np.allclose(arr[:,:,0], arr[:,:,1], atol=5)
                    g_eq_b = np.allclose(arr[:,:,1], arr[:,:,2], atol=5)
                    assert r_eq_g and g_eq_b, f"Chart {r.path} has color-only differentiation (R!=G!=B)"

    def test_trend_chart_included(self):
        from technical_report_writer import generate_charts
        data = _sample_aggregated_data()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            refs = generate_charts(data, out)
            types = [r.type for r in refs]
            assert "line" in types, "Per-student trend chart should be included"

    def test_performance_aggregate(self):
        from technical_report_writer import aggregate_data, validate_input_files
        import time
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for i in range(10):
                d = _valid_errant_dict()
                d["student_id"] = f"{12340 + i}"
                d["class"] = f"M{2 if i < 5 else 3}A"
                (p / f"stu{i}.json").write_text(json.dumps(d), encoding="utf-8")
            vr = validate_input_files(p)
            start = time.time()
            result = aggregate_data(vr.valid_files)
            elapsed = time.time() - start
            assert result.meta.n_students == 10
            assert elapsed < 5.0, f"Aggregation took {elapsed:.2f}s (expected <5s)"

    def test_performance_charts(self):
        from technical_report_writer import generate_charts
        import time
        data = _sample_aggregated_data()
        with tempfile.TemporaryDirectory() as tmp:
            start = time.time()
            refs = generate_charts(data, Path(tmp))
            elapsed = time.time() - start
            assert len(refs) >= 3
            assert elapsed < 30.0, f"Chart generation took {elapsed:.2f}s (expected <30s)"


class TestRenderTechnicalReport:
    def test_markdown_to_html_conversion(self):
        from technical_report_writer import _parse_sections
        md = """## Introduction
This is a **bold** intro paragraph.

## Findings
- Point one
- Point two

## References
```json
[{"authors": "Ellis, R.", "year": "2008", "title": "SLA Study", "source": "OUP", "doi": ""}]
```"""
        sections, refs = _parse_sections(md)
        assert len(sections) == 3
        assert sections[0]["id"] == "introduction"
        assert "<strong>" in sections[0]["body"]
        assert "<ul>" in sections[1]["body"]
        assert len(refs) == 1
        assert refs[0].authors == "Ellis, R."

    def test_section_splitting_headings(self):
        from technical_report_writer import _parse_sections
        md = "Preamble text\n\n## Section One\nBody\n\n## Section Two\nMore"
        sections, refs = _parse_sections(md)
        assert len(sections) == 2
        assert sections[0]["title"] == "Section One"
        assert sections[1]["title"] == "Section Two"

    def test_empty_references(self):
        from technical_report_writer import _parse_sections
        md = "## Intro\nNo refs.\n\n## References\nNo code fence."
        sections, refs = _parse_sections(md)
        assert len(refs) == 0

    def test_missing_template_raises(self):
        from technical_report_writer import render_technical_report
        data = _sample_aggregated_data()
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            draft.write_text("## Test\nBody", encoding="utf-8")
            with pytest.raises(FileNotFoundError):
                render_technical_report(draft, data, Path(tmp) / "out.pdf", template_path=Path("/nonexistent/template.html"))


class TestCLI:
    def test_validate_subcommand(self, capsys):
        from contextlib import suppress
        from technical_report_writer import main
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            d = _valid_errant_dict()
            (p / "data.json").write_text(json.dumps(d), encoding="utf-8")
            with suppress(SystemExit):
                main(["validate", str(p)])
            captured = capsys.readouterr()
            assert "1 valid" in captured.out or "1 file" in captured.out or "valid" in captured.out.lower()

    def test_aggregate_subcommand(self, capsys):
        from contextlib import suppress
        from technical_report_writer import main
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            d = _valid_errant_dict()
            (p / "data.json").write_text(json.dumps(d), encoding="utf-8")
            with suppress(SystemExit):
                main(["aggregate", str(p)])
            captured = capsys.readouterr()
            assert "students" in captured.out.lower() or "aggregate" in captured.out.lower()

    def test_charts_subcommand(self, capsys):
        from contextlib import suppress
        from technical_report_writer import main
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            out = Path(tmp) / "charts_out"
            d = _valid_errant_dict()
            (p / "data.json").write_text(json.dumps(d), encoding="utf-8")
            with suppress(SystemExit):
                main(["charts", str(p), str(out)])
            captured = capsys.readouterr()
            assert "chart" in captured.out.lower()

    def test_render_subcommand_missing_draft(self, capsys):
        from contextlib import suppress
        from technical_report_writer import main
        with suppress(SystemExit):
            main(["render", "/nonexistent/draft.md", "/tmp/out.pdf"])
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "error" in captured.out.lower()


class TestCitationAnnotation:
    def test_annotate_missing_file(self):
        from technical_report_writer import annotate_source_pdf, CitationSpan
        result = annotate_source_pdf(
            Path("/tmp/nonexistent_xyz.pdf"),
            [CitationSpan(source_path=Path("/tmp/nonexistent_xyz.pdf"), page=1, text="test", section="Intro", citation_text="(Test, 2020, p. 1)")],
            Path("/tmp"),
        )
        assert result is None

    def test_annotate_scanned_pdf(self):
        from technical_report_writer import annotate_source_pdf, CitationSpan
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "blank.png"
            from PIL import Image
            Image.new("RGB", (100, 100), "white").save(img_path)
            pdf_path = Path(tmp) / "scanned.pdf"
            from PIL import Image
            img = Image.new("RGB", (100, 100), "white")
            img.save(pdf_path, "PDF", resolution=72)
            result = annotate_source_pdf(
                pdf_path,
                [CitationSpan(source_path=pdf_path, page=1, text="nothing", section="Intro", citation_text="(Test, 2020)")],
                Path(tmp) / "annotated",
            )
            assert result is None

    def test_citation_map_generated(self):
        from technical_report_writer import generate_citation_map
        with tempfile.TemporaryDirectory() as tmp:
            annotated = Path(tmp) / "annotated"
            annotated.mkdir()
            (annotated / "test-annotated.pdf").write_text("")
            out = Path(tmp) / "citation-map.md"
            result = generate_citation_map(
                {"Intro": [("(Test, 2020, p. 5)", "test-annotated.pdf", 5, "Some passage")]},
                annotated,
                out,
            )
            assert result.exists()
            text = result.read_text(encoding="utf-8")
            assert "## Section: Intro" in text
            assert "(Test, 2020, p. 5)" in text
            assert "Some passage" in text
        from technical_report_writer import generate_charts
        from PIL import Image
        import numpy as np
        data = _sample_aggregated_data()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            refs = generate_charts(data, out)
            for r in refs:
                img = Image.open(r.path).convert("RGB")
                arr = np.array(img)
                if arr.size > 0:
                    non_text = arr  # Check all pixels
                    r_eq_g = np.allclose(non_text[:,:,0], non_text[:,:,1], atol=5)
                    g_eq_b = np.allclose(non_text[:,:,1], non_text[:,:,2], atol=5)
                    assert r_eq_g and g_eq_b, f"Chart {r.path} has color-only differentiation (R!=G!=B)"
