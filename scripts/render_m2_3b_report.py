#!/usr/bin/env python3
"""Render the M2-3B lexico-grammatical report.

Aggregates ONLY the M2-3B local-working files and renders the Markdown
draft through a section-driven template (tech_report.html is fully
hard-coded for the M2/M3 comparison report and ignores draft sections).
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")

from technical_report_writer import (
    aggregate_data,
    render_technical_report,
)

DRAFT = Path("outputs/drafts/m2-3b-lexico-grammatical-needs.md")
OUTPUT = Path("PDF/ARCHIVE/CDP REPORT/m2-3b-lexico-grammatical-needs.pdf")
TEMPLATE = Path("templates/m2_3b_report.html")


def main() -> None:
    files = sorted(Path("local-working").glob("M2-3B-9*.json"))
    if not files:
        print("No M2-3B local-working files found")
        sys.exit(1)

    valid = []
    for f in files:
        try:
            import json
            raw = json.loads(f.read_text(encoding="utf-8"))
            if raw.get("error_rate") is not None:
                valid.append(f)
        except Exception as e:
            print(f"  skipping {f.name}: {e}")

    data = aggregate_data(valid)
    render_technical_report(data, OUTPUT, template_path=TEMPLATE, draft_path=DRAFT)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    main()
