import json
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FileValidationError(BaseModel):
    field: str
    message: str


class InvalidFile(BaseModel):
    path: Path
    errors: list[FileValidationError]


class ValidationResult(BaseModel):
    valid_files: list[Path]
    invalid_files: list[InvalidFile]
    total_checked: int


class ReportMeta(BaseModel):
    title: str
    generated_at: str
    n_students: int
    n_classes: int
    cohorts: list[str]
    date_range: tuple[str, str]


class StudentSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: str
    name: str
    class_: str = Field(alias="class")
    word_count: int
    error_rate: int | None = None
    cefr_level: str
    error_count: int
    top_errors: list[dict] = []

    @field_validator("student_id")
    @classmethod
    def five_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError(f"student_id must be 5 digits, got '{v}'")
        return v

    @field_validator("error_rate")
    @classmethod
    def range_check(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"error_rate must be 0-100 or None, got {v}")
        return v


class ErrorCodeBucket(BaseModel):
    code: str
    supercategory: str
    name: str
    count: int
    percentage: float


class CohortBucket(BaseModel):
    cohort: str
    n_students: int
    mean_error_rate: float
    median_error_rate: float
    std_error_rate: float
    min_error_rate: float
    max_error_rate: float


class OverallStats(BaseModel):
    n_students: int
    mean_error_rate: float
    median_error_rate: float
    std_error_rate: float
    min_error_rate: float
    max_error_rate: float
    mean_word_count: float
    b1_count: int
    b2_count: int


class ChartRef(BaseModel):
    section: str
    path: Path
    caption: str
    type: str


class ReportSection(BaseModel):
    id: str
    title: str
    rhetorical_question: str | None = None
    body: str = ""
    charts: list[ChartRef] = []
    tables: list[dict] = []
    is_baseline: bool = True


class ReferenceEntry(BaseModel):
    authors: str
    year: str
    title: str
    source: str
    doi: str = ""
    formatted: str = ""


class TechReportTemplateContext(BaseModel):
    masthead_left: str
    masthead_center: str
    masthead_right: str
    report_title: str
    generated_at: str
    sections: list[ReportSection]
    references: list[ReferenceEntry]
    appendix_tables: list[dict]
    data: AggregatedReportData | None = None


class AggregatedReportData(BaseModel):
    meta: ReportMeta
    students: list[StudentSummary]
    error_code_summary: list[ErrorCodeBucket]
    cohort_summary: list[CohortBucket]
    overall_stats: OverallStats
    charts: list[ChartRef]


class CitationSpan(BaseModel):
    source_path: Path
    page: int
    text: str
    section: str
    citation_text: str


class CitationMapEntry(BaseModel):
    citation_text: str
    source_file: str
    page: int
    quoted_passage: str


def validate_input_files(data_path: Path) -> ValidationResult:
    if not data_path.exists():
        raise FileNotFoundError(f"Data path does not exist: {data_path}")
    json_files = sorted(data_path.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found at {data_path}")
    from pydantic import ValidationError
    from models import ErrantOutput
    valid = []
    invalid = []
    for f in json_files:
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            ErrantOutput.model_validate(raw)
            valid.append(f)
        except ValidationError as exc:
            errs = []
            for e in exc.errors():
                field = ".".join(str(p) for p in e.get("loc", []))
                errs.append(FileValidationError(field=field or "root", message=e.get("msg", str(e))))
            invalid.append(InvalidFile(path=f, errors=errs))
        except Exception as exc:
            errs = [FileValidationError(field="root", message=str(exc))]
            invalid.append(InvalidFile(path=f, errors=errs))
    return ValidationResult(
        valid_files=valid,
        invalid_files=invalid,
        total_checked=len(json_files),
    )


def _infer_cefr(cohort: str) -> str:
    c = cohort.upper()
    if c.startswith("M3") or c.startswith("M4") or c.startswith("M5") or c.startswith("M6"):
        return "B2"
    return "B1"


def aggregate_data(valid_files: list[Path]) -> AggregatedReportData:
    if not valid_files:
        raise ValueError("No valid files to aggregate")
    import json
    from models import ErrantOutput
    from datetime import datetime

    students_raw = []
    code_counts: dict[str, int] = {}
    cohort_data: dict[str, list[int]] = {}
    b1_count = 0
    b2_count = 0
    dates = []
    classes = set()

    for f in valid_files:
        raw = json.loads(f.read_text(encoding="utf-8"))
        validated = ErrantOutput.model_validate(raw)
        students_raw.append(validated)

    for s in students_raw:
        cohort_key = s.class_[:2].upper() if len(s.class_) >= 2 else "UNK"
        for err in s.errant_analysis.errors:
            code = err.get("type", "UNK")
            code_counts[code] = code_counts.get(code, 0) + err.get("count", 1)
        cohort_data.setdefault(cohort_key, []).append(s.error_rate or 0)
        classes.add(s.class_)
        cefr = _infer_cefr(cohort_key)
        if cefr == "B1":
            b1_count += 1
        else:
            b2_count += 1
        if s.submission_date:
            dates.append(s.submission_date)

    total = len(students_raw)
    rates_all = [s.error_rate or 0 for s in students_raw]
    mean_rate = sum(rates_all) / total if total else 0.0
    sorted_rates = sorted(rates_all)
    median_rate = sorted_rates[total // 2] if total else 0.0
    variance = sum((r - mean_rate) ** 2 for r in rates_all) / total if total else 0.0
    word_counts = [s.word_count for s in students_raw]

    cohort_buckets = []
    for cohort, rates in sorted(cohort_data.items()):
        n = len(rates)
        cm = sum(rates) / n if n else 0.0
        sr = sorted(rates)
        cmed = sr[n // 2] if n else 0.0
        cv = sum((r - cm) ** 2 for r in rates) / n if n else 0.0
        cohort_buckets.append(CohortBucket(
            cohort=cohort,
            n_students=n,
            mean_error_rate=round(cm, 2),
            median_error_rate=round(cmed, 2),
            std_error_rate=round(cv ** 0.5, 2),
            min_error_rate=round(min(rates), 2),
            max_error_rate=round(max(rates), 2),
        ))

    total_errors = sum(code_counts.values())
    error_buckets = []
    from config import ERRANT_CODE_NAMES
    for code, count in sorted(code_counts.items(), key=lambda x: -x[1]):
        supercat = code.split(":")[0] if ":" in code else code
        name = ERRANT_CODE_NAMES.get(code, code)
        pct = round(count / total_errors * 100, 1) if total_errors else 0.0
        error_buckets.append(ErrorCodeBucket(
            code=code, supercategory=supercat, name=name, count=count, percentage=pct,
        ))

    student_summaries = []
    for s in students_raw:
        cohort_key = s.class_[:2].upper() if len(s.class_) >= 2 else "UNK"
        cefr = _infer_cefr(cohort_key)
        err_count = len(s.errant_analysis.errors)
        top = sorted(
            s.errant_analysis.errors,
            key=lambda e: e.get("count", 1),
            reverse=True,
        )[:3]
        student_summaries.append(StudentSummary(
            student_id=s.student_id,
            name=s.name,
            class_=s.class_,
            word_count=s.word_count,
            error_rate=s.error_rate,
            cefr_level=cefr,
            error_count=err_count,
            top_errors=[{"code": e.get("type"), "type": e.get("type")} for e in top],
        ))

    date_range = (min(dates), max(dates)) if dates else ("", "")

    return AggregatedReportData(
        meta=ReportMeta(
            title="",
            generated_at=datetime.now().isoformat(),
            n_students=total,
            n_classes=len(classes),
            cohorts=sorted(cohort_data.keys()),
            date_range=date_range,
        ),
        students=student_summaries,
        error_code_summary=error_buckets,
        cohort_summary=cohort_buckets,
        overall_stats=OverallStats(
            n_students=total,
            mean_error_rate=round(mean_rate, 2),
            median_error_rate=round(median_rate, 2),
            std_error_rate=round(variance ** 0.5, 2),
            min_error_rate=round(min(rates_all), 2),
            max_error_rate=round(max(rates_all), 2),
            mean_word_count=round(sum(word_counts) / total, 1) if total else 0.0,
            b1_count=b1_count,
            b2_count=b2_count,
        ),
        charts=[],
    )


def generate_charts(data: AggregatedReportData, output_dir: Path) -> list[ChartRef]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir = Path(output_dir)
    chart_dir = output_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    refs: list[ChartRef] = []

    # Chart 1: ERRANT Code Frequency (horizontal bar)
    if data.error_code_summary:
        codes = data.error_code_summary[:10]
        labels = [c.name[:30] for c in reversed(codes)]
        counts = [c.count for c in reversed(codes)]
        supercats = [c.supercategory for c in reversed(codes)]
        fig, ax = plt.subplots(figsize=(6, max(3, len(labels) * 0.4)))
        colors = {"R": "0.3", "M": "0.5", "U": "0.7"}
        hatches = {"R": "", "M": "//", "U": ".."}
        bars = ax.barh(labels, counts, color=[colors.get(s, "0.5") for s in supercats])
        for bar, sc in zip(bars, supercats):
            bar.set_hatch(hatches.get(sc, ""))
        ax.set_xlabel("Error count", fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8)
        fig.tight_layout()
        path = chart_dir / "errant-code-frequency.svg"
        fig.savefig(path, format="svg")
        plt.close(fig)
        refs.append(ChartRef(section="findings", path=path, caption="Error frequency by ERRANT code category", type="bar"))

    # Chart 2: Cohort Comparison (grouped bar)
    if len(data.cohort_summary) >= 2:
        cohorts = [c.cohort for c in data.cohort_summary]
        means = [c.mean_error_rate for c in data.cohort_summary]
        fig, ax = plt.subplots(figsize=(5, 3))
        x = np.arange(len(cohorts))
        hatch_patterns = ["", "//", "x"]
        for i, (cohort, mean) in enumerate(zip(cohorts, means)):
            h = hatch_patterns[i % len(hatch_patterns)]
            ax.bar(x[i], mean, width=0.5, color="0.4", hatch=h, label=cohort)
        ax.set_xticks(x)
        ax.set_xticklabels(cohorts, fontsize=9)
        ax.set_ylabel("Mean error rate (%)", fontsize=9)
        ax.legend(fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        path = chart_dir / "cohort-comparison.svg"
        fig.savefig(path, format="svg")
        plt.close(fig)
        refs.append(ChartRef(section="findings", path=path, caption="Error rate comparison by cohort", type="grouped_bar"))

    # Chart 3: Error Rate Distribution (histogram)
    if data.overall_stats.n_students >= 10:
        rates = [s.error_rate or 0 for s in data.students]
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.hist(rates, bins=range(0, 105, 5), color="0.5", edgecolor="black", hatch="|")
        ax.set_xlabel("Error rate (%)", fontsize=9)
        ax.set_ylabel("Number of students", fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8)
        fig.tight_layout()
        path = chart_dir / "error-rate-distribution.svg"
        fig.savefig(path, format="svg")
        plt.close(fig)
        refs.append(ChartRef(section="findings", path=path, caption="Distribution of student error rates", type="histogram"))

    # Chart 4: Per-student trend line (individual history)
    from config import B1_TARGET, B2_TARGET
    for s in data.students:
        if s.error_count < 1 or s.error_rate is None:
            continue
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.plot([0, 1], [s.error_rate or 0, s.error_rate or 0],
                marker="o", linestyle="-", linewidth=1.5, color="#333333")
        cefr = s.cefr_level
        target = B1_TARGET if cefr == "B1" else B2_TARGET
        ax.axhline(y=target, color="#555555", linestyle="--", linewidth=1, label=f"Target ({cefr})")
        ax.set_ylabel("Error rate (%)", fontsize=8)
        ax.set_xlim(-0.2, 1.2)
        ax.set_xticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8)
        ax.legend(fontsize=7)
        fig.tight_layout()
    if data.students:
        fig, ax = plt.subplots(figsize=(5, 3))
        ids = [s.student_id for s in data.students]
        rates = [s.error_rate or 0 for s in data.students]
        ax.plot(ids, rates, marker="o", linestyle="-", linewidth=1.5, color="#333333")
        ax.set_ylabel("Error rate (%)", fontsize=9)
        ax.set_xticks(range(len(ids)))
        ax.set_xticklabels(ids, fontsize=6, rotation=45)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8)
        fig.tight_layout()
        path = chart_dir / "per-student-trend.svg"
        fig.savefig(path, format="svg")
        plt.close(fig)
        refs.append(ChartRef(section="findings", path=path, caption="Per-student error rate overview", type="line"))

    return refs


def _parse_sections(markdown_text: str) -> tuple[list[dict], list[ReferenceEntry]]:
    from markdown_it import MarkdownIt
    md_parser = MarkdownIt("commonmark")
    lines = markdown_text.split("\n")
    sections: list[dict] = []
    refs: list[ReferenceEntry] = []
    current_title = ""
    current_body_lines: list[str] = []
    in_references = False
    in_ref_code_fence = False
    ref_code_lines: list[str] = []

    def flush_section():
        nonlocal current_title, current_body_lines
        if current_title:
            body_text = "\n".join(current_body_lines).strip()
            html_body = md_parser.render(body_text) if body_text else ""
            section_id = current_title.lower().replace("?", "").replace(" ", "-").replace(":", "")[:40]
            sections.append({
                "id": section_id,
                "title": current_title,
                "body": html_body,
                "charts": [],
                "tables": [],
                "is_baseline": True,
            })

    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("## "):
            flush_section()
            current_title = stripped[3:].strip()
            current_body_lines = []
            in_references = current_title.lower() == "references"
            in_ref_code_fence = False
            ref_code_lines = []
        elif in_references and stripped.startswith("```"):
            if in_ref_code_fence:
                in_ref_code_fence = False
                try:
                    raw_refs = json.loads("\n".join(ref_code_lines))
                    for r in raw_refs:
                        refs.append(ReferenceEntry.model_validate(r))
                except (json.JSONDecodeError, Exception):
                    pass
                ref_code_lines = []
            else:
                in_ref_code_fence = True
        elif in_ref_code_fence:
            ref_code_lines.append(stripped)
        elif current_title:
            current_body_lines.append(line)
    flush_section()

    return sections, refs


def render_technical_report(
    aggregated_data: AggregatedReportData,
    output_path: Path,
    template_path: Path = Path("templates/tech_report.html"),
    draft_path: Path | None = None,
) -> Path:
    from datetime import datetime
    from jinja2 import Environment, FileSystemLoader
    from playwright.sync_api import sync_playwright

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    project_root = Path(__file__).resolve().parent.parent

    def _img_b64(rel_path: str) -> str:
        img_path = project_root / rel_path
        if not img_path.exists():
            return ""
        import base64, mimetypes
        raw = img_path.read_bytes()
        mime = mimetypes.guess_type(str(img_path))[0] or "image/png"
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}"

    sections = []
    refs: list[ReferenceEntry] = []

    if draft_path and draft_path.exists():
        md_text = draft_path.read_text(encoding="utf-8")
        sections, refs = _parse_sections(md_text)

    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    tmpl = env.get_template(template_path.name)

    context = TechReportTemplateContext(
        masthead_left=_img_b64("images/ACT.png"),
        masthead_center="C·E·L Mathayom",
        masthead_right=_img_b64("images/cambridge.png"),
        report_title=aggregated_data.meta.title,
        generated_at=datetime.now().strftime("%B %d, %Y"),
        sections=sections,
        references=refs,
        appendix_tables=[],
        data=aggregated_data,
    )
    html = tmpl.render(context=context)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.emulate_media(media="print")
            page.pdf(
                path=str(output_path),
                format="A4",
                margin={"top": "0cm", "bottom": "0cm", "left": "0cm", "right": "0cm"},
                print_background=True,
                display_header_footer=True,
                footer_template='<div style="font-size:9pt; text-align:center; width:100%; color:#666;"><span class="pageNumber"></span></div>',
            )
            browser.close()
    except ImportError:
        raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")
    try:
        flattened = output_path.with_stem(output_path.stem + "-flattened")
        subprocess.run(
            ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
             "-dPDFSETTINGS=/default", "-dNOPAUSE", "-dQUIET", "-dBATCH",
             f"-sOutputFile={flattened}", str(output_path)],
            capture_output=True, timeout=60,
        )
        if flattened.exists():
            flattened.replace(output_path)
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return output_path


def annotate_source_pdf(
    source_path: Path,
    citations: list[CitationSpan],
    output_dir: Path,
) -> Path | None:
    try:
        import fitz
    except ImportError:
        return None
    if not source_path.exists():
        return None
    try:
        doc = fitz.open(source_path)
    except Exception:
        return None
    if doc.page_count == 0:
        doc.close()
        return None
    has_text = any(p.get_text().strip() for p in doc)
    if not has_text:
        doc.close()
        return None
    for cs in citations:
        if cs.page < 1 or cs.page > doc.page_count:
            continue
        page = doc[cs.page - 1]
        text = page.get_text()
        idx = text.find(cs.text)
        if idx < 0:
            continue
        rects = page.search_for(cs.text)
        for rect in rects:
            page.add_highlight_annot(rect)
            annot = page.add_text_annot(rect.tr, f"Cited in: {cs.section}")
            if annot:
                annot.set_info(title="Citation")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem.replace(" ", "-")
    out_path = output_dir / f"{stem}-annotated.pdf"
    doc.save(out_path, garbage=4, deflate=True)
    doc.close()
    return out_path


def generate_citation_map(
    citations_by_section: dict[str, list[tuple[str, str, int, str]]],
    annotated_dir: Path,
    output_path: Path,
) -> Path:
    lines = []
    lines.append("# Citation Map\n")
    for section, entries in citations_by_section.items():
        lines.append(f"## Section: {section}\n")
        for cit_text, source_file, page, passage in entries:
            rel_path = Path(annotated_dir) / source_file
            lines.append(f"- {cit_text} → `{rel_path}`, page {page}")
            lines.append(f"  > \"{passage}\"\n")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Technical Report Writer")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate", help="Validate input JSON files")
    validate_p.add_argument("path", type=Path)

    aggregate_p = sub.add_parser("aggregate", help="Aggregate error statistics")
    aggregate_p.add_argument("path", type=Path)

    charts_p = sub.add_parser("charts", help="Generate grayscale charts")
    charts_p.add_argument("path", type=Path)
    charts_p.add_argument("output_dir", type=Path)

    render_p = sub.add_parser("render", help="Render PDF from Markdown draft")
    render_p.add_argument("draft", type=Path)
    render_p.add_argument("output", type=Path)

    args = parser.parse_args(argv)

    if args.command == "validate":
        try:
            result = validate_input_files(args.path)
            print(f"Checked {result.total_checked} file(s): {len(result.valid_files)} valid, {len(result.invalid_files)} invalid")
            for inv in result.invalid_files:
                for e in inv.errors:
                    print(f"  {inv.path.name}: {e.field} — {e.message}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "aggregate":
        try:
            vr = validate_input_files(args.path)
            if not vr.valid_files:
                print("No valid files to aggregate")
                sys.exit(1)
            data = aggregate_data(vr.valid_files)
            print(f"Aggregated {data.meta.n_students} students across {data.meta.n_classes} classes")
            print(f"  Cohorts: {', '.join(data.meta.cohorts)}")
            print(f"  Mean error rate: {data.overall_stats.mean_error_rate}%")
            print(f"  Error code categories: {len(data.error_code_summary)}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "charts":
        try:
            vr = validate_input_files(args.path)
            if not vr.valid_files:
                print("No valid files to chart")
                sys.exit(1)
            data = aggregate_data(vr.valid_files)
            refs = generate_charts(data, args.output_dir)
            print(f"Generated {len(refs)} chart(s) in {args.output_dir / 'charts'}/")
            for r in refs:
                print(f"  {r.type}: {r.path.name}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "render":
        try:
            from pathlib import Path as _Path
            data_dir = _Path("local-working")
            if not data_dir.exists():
                print(f"Data directory not found: {data_dir}")
                sys.exit(1)
            vr = validate_input_files(data_dir)
            valid = vr.valid_files
            if not valid:
                print("No valid data files found in local-working/")
                sys.exit(1)
            data = aggregate_data(valid)
            draft_p = args.draft if args.draft and args.draft.exists() else None
            render_technical_report(data, args.output, draft_path=draft_p)
            print(f"PDF generated: {args.output}")
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
