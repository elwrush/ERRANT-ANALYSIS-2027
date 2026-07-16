# Technical Report Writer

## Feature Summary

An interactive CLI report-writer that generates professional technical assessment reports from pre-existing ERRANT analysis JSONs. The report writer is purely a rendering/presentation layer — it does NOT perform ERRANT analysis, correction, or ingestion. The agent (Kilo) orchestrates the entire report-writing workflow: it interacts with the user, composes the report content (prose, analysis, recommendations), generates charts, and delegates only the final HTML→PDF rendering to Jinja2+Playwright. The user is guided through a structured workflow: they provide the data location (already-analysed JSONs), report title, and optional additional sections; the agent produces a Markdown first draft for review, then renders the final PDF. The report uses the school's document header and is designed for grayscale printing.

---

## User Stories

| Priority | Story |
|----------|-------|
| P1 | As a teacher, I want to generate a technical report from errant analysis data by specifying where the data live, so I can produce a classroom-ready document without manual formatting. |
| P1 | As a teacher, I want the report to include charts and graphs that illustrate error patterns, so findings are visually clear and actionable. |
| P1 | As a school coordinator, I want all charts to use grayscale-safe patterns (crosshatching, dots, stripes) instead of color-only differentiation, so the report prints clearly on a monochrome printer. |
| P1 | As a reader, I want the report written in plain, active language that explains lexico-grammatical findings clearly, without "AI slop" phrasing or forced informality. |
| P2 | As a teacher, I want to add custom sections to the report by specifying a rhetorical question and insertion point, so the report addresses my specific classroom concerns. |
| P2 | As a reviewer, I want a first draft in Markdown format that I can review and annotate before the final PDF is generated, so I can verify all sources and fix errors early. |
| P2 | As a reader, I want all referenced sources to include page or paragraph numbers, so claims can be verified against source material. |
| P3 | As a developer, I want the report writer to research rhetorical best practices via Tavily before writing, so the tone is professional and avoids common AI writing patterns. |
| P3 | As a school leader, I want the report to benchmark student proficiency against international standards (CEFR, Cambridge English), so the findings are contextualised for external stakeholders. |

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | The system MUST provide a CLI command `/write-technical-report` that initiates an interactive session. |
| FR-002 | The interactive session MUST ask the user in this order: (a) path to the data directory/JSONs, (b) report title, (c) whether additional sections beyond the baseline are needed; if yes, list the baseline sections and prompt for rhetorical question + insertion point. |
| FR-003 | When asking about additional sections, the system MUST list the baseline sections and allow the user to specify a rhetorical question and where to insert it. |
| FR-004 | The report MUST include the following baseline sections: Introduction, What are the most important findings?, How was the report compiled?, What does this report say about our students' proficiency?, How can teachers use this report?, What is involved in an ERRANT Analysis?, What are the limitations of ERRANT Analysis?, Future directions, Appendix: Data in detail, Technical details, References. |
| FR-005 | The report MUST use the Jinja2→Playwright→PDF pipeline (NOT Pandoc→Typst). |
| FR-006 | The report MUST replicate the masthead/logo band layout from the existing WRITING_ASSESSMENT_NEW templates: three-column grid with `cambridge.png` left, "C·E·L Mathayom" centered, `ACT.png` right, and a separator line below. Logo files must be loaded from the local `images/` directory. |
| FR-007 | All charts and graphs MUST use grayscale-safe visual cues (crosshatching, dot patterns, line styles) — no color-only differentiation. |
| FR-008 | Before generating prose, the agent MUST use the Tavily search skill (via Kilo's builtin capability) to compile a list of rhetorical best practices for professional/technical writing, and apply these rules to avoid "AI slop" phrasing (em dashes, clichés, hedging). |
| FR-009 | The authorial voice MUST be that of an educated Australian teacher explaining lexico-grammatical findings. Active voice preferred. Bullet points where appropriate. Do NOT use Australianisms ("mate", "no worries", etc.). |
| FR-010 | The system MUST produce a Markdown first draft for human review. Only after the user types an explicit sign-off command (e.g. "proceed", "generate", "sign off", or explicit confirmation) shall the final PDF be generated. If the user declines or cancels, the draft MUST be saved to `outputs/drafts/` with the note "DRAFT — not signed off" appended to the filename. |
| FR-011 | Every referenced source in the report MUST include page numbers or paragraph numbers for verification. For each source PDF referenced, the agent MUST: (a) produce an annotated copy with highlights on cited passages plus sticky annotations indicating the report section that cites them, saved to `references/annotated/`; (b) generate a `references/citation-map.md` that maps each inline citation to the source file, page number, and highlighted passage text. (FR-011 governs inline citation formatting and source verification; FR-014 governs the reference list.) |
| FR-012 | The report MUST include charts that break down errors by ERRANT code category, cohort comparison, and error frequency. |
| FR-013 | Before composing the report, the agent MUST validate all input JSONs against Pydantic models (via a Python helper script) to ensure data integrity. |
| FR-014 | The References section MUST be formatted in APA 7th edition style (hanging indent, author–date format, italicized periodical titles, DOI/URL where applicable). Reference entries MUST be provided as a JSON code fence in the Markdown draft (` ```json [{...}] ``` `) with per-entry `authors`, `year`, `title`, `source`, and `doi` fields, then rendered as styled HTML by the template. (FR-014 governs the reference list; FR-011 governs inline citations and source verification.) |

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Report compiles without errors | `python src/technical_report_writer.py render <draft> <output>` exits 0 and produces a non-empty PDF |
| All 11 baseline sections present | Text extraction from PDF confirms section headings present |
| No Typst/Pandoc dependency | `requirements.txt` contains no `typst`, `pandoc`, or `pypdf` |
| Charts use grayscale-safe patterns | Automated pixel check: all rendered chart-image pixels have equal R/G/B channels (no color-only differentiation); chart bar fills use hatching patterns (`//`, `..`, `x`, `|`) |
| First draft in Markdown | `.md` file produced in outputs/ before any `.pdf` |
| Human review gate enforced | Pipeline pauses after `.md` generation, presents draft path to user, waits for an explicit sign-off command ("proceed", "generate", "sign off") or cancellation; no PDF produced without explicit user confirmation |
| All references include page numbers | Grep of markdown draft confirms pattern `(p\. \d+)` or `(para\. \d+)` |
| Source PDFs annotated | `references/annotated/` contains one annotated PDF per source, with highlights and sticky annotations on cited passages |
| Citation map generated | `references/citation-map.md` exists and maps every inline citation to source file, page, and quoted text |
| Tavily search invoked | Logs confirm `tavily-search` skill was called before prose generation |
| Authorial voice matches spec | Markdown draft contains no prohibited Australianisms ("mate", "no worries", "g'day", "bloody"), no em dashes used as crutch punctuation, active voice preferred (grep for passive voice frequency <20% of sentences) |
| Agent internal LLM calls use response_format | All agent-internal LLM calls for report content must use `response_format={"type": "json_object"}` (via Kilo's builtin compliance) |
| Pydantic validation on data load | `model_validate()` called on input JSONs before processing |

---

## Edge Cases

| Case | Expected handling |
|------|-------------------|
| Data directory is empty or missing | Clear error message: "No JSON files found at <path>. Please check the path and try again." |
| JSON files fail Pydantic validation | Log which file(s) failed and which fields; offer to skip or abort |
| No chart-worthy data (single student, one cohort) | Generate summary stats as a table instead of chart; note limitation in report |
| Tavily API unavailable | Log warning, proceed with a default style guide (Strunk & White principles); do not block pipeline |
| User cancels at human review gate | Save draft `.md` to outputs/ with note "DRAFT — not signed off"; exit cleanly |
| Report title contains special characters | Sanitize for filename safety (strip `\/:*?"<>|`) before creating output path |
| Additional section insertion point conflicts (two sections at same position) | Ask user to re-specify; accept only one section per insertion point |
| Header template files missing from `WRITING_ASSESSMENT_NEW` | Log warning, fall back to a minimal header (school name + logo if available) |
| Source PDF not found for a cited reference | Log warning, skip annotation for that source and note in citation-map.md: "Source not available for annotation" |
| Source PDF is scanned/image-only (no text layer) | Log warning, skip annotation for that source, note in citation-map.md: "Scanned PDF — no text layer for annotation" |
| Source PDF encrypted or permission-protected | Log warning, skip annotation for that source, note in citation-map.md: "Permission-protected — could not annotate" |

---

## Non-Functional Requirements

| ID | Requirement | Measurement |
|----|-------------|-------------|
| NFR-001 | Full report generation (with chart rendering) must complete within 120 seconds on a typical developer machine (8-core, 16 GB RAM, SSD) | `time python src/technical_report_writer.py render <draft> <output>` < 120s wall-clock |
| NFR-002 | Playwright Chromium headless must not consume more than 500 MB RSS during PDF generation | `psutil` measurement during `html_to_pdf()` |
| NFR-003 | The Markdown draft must be produced within 30 seconds of user confirming data location and title | Wall-clock timing of draft generation step |
| NFR-004 | Report PDF must be printable on A4 paper with 1.6cm margins (matching existing WRITING_ASSESSMENT_NEW templates) | PDF page size check (`PyMuPDF`) confirms 595.28 × 841.89 pts |

---

## Key Entities

| Entity | Description |
|--------|-------------|
| Report session | The interactive workflow instance: data path, title, custom sections, human-review state |
| Report section | A named section with a rhetorical question heading, body content, and optional charts |
| Data source | Directory of student ERRANT analysis JSON files, validated via Pydantic models |
| Chart renderer | Generates grayscale-safe bar/column charts from error-code frequency data |
| Markdown draft | First-pass `.md` output for human review before final PDF |
| Jinja2/Playwright renderer | Final PDF generation pipeline (Markdown → HTML via `markdown-it-py` → Jinja2 template → Playwright PDF) |
| Tavily style guide | Output of Tavily search: rhetorical rules to guide prose generation |
| Human review gate | Checkpoint between Markdown draft and final PDF generation |
| ReferenceEntry | Structured APA 7th reference entry (`authors`, `year`, `title`, `source`, `doi`) stored as JSON in the References code fence |
| CitationSpan | A specific text passage in a source PDF that is cited, with page number and report section name |
| CitationMapEntry | Maps an inline citation to its annotated source PDF, page number, and quoted passage |
| Annotated PDF | Source PDF with yellow highlights on cited passages and sticky annotations indicating the citing report section |

---

## Assumptions

| # | Assumption | Confidence |
|---|------------|------------|
| 1 | The data JSONs follow the `ErrantOutput` schema defined in `src/models.py` — `student_id`, `original_text`, `corrected_text`, `error_rate` (int 0–100 or None), `class_` (prefix M2/M3 determines cohort), `errant_analysis.errors[]` with `error_code` per item. | Medium — confirm schema before first run |
| 2 | The document header from `C:\PROJECTS\WRITING_ASSESSMENT_NEW` is a Jinja2 HTML/CSS template that can be extended or imported. | Confirmed |
| 3 | The Tavily API key is configured in the environment and the skill is accessible from the project directory. | Confirmed |
| 4 | The existing logo images (`ACT.png`, `cambridge.png`) and masthead layout from `C:\PROJECTS\WRITING_ASSESSMENT_NEW` serve as the design reference for the report header. | Confirmed |

---

## Clarifications (2026-07-14)

| # | Question | Resolution | Impact on Spec |
|---|----------|------------|----------------|
| 1 | What format is the document header in `C:\PROJECTS\WRITING_ASSESSMENT_NEW`? | **Jinja2 HTML/CSS template** — confirmed by user. | FR-006: the report Jinja2 template must replicate the three-column masthead layout (cambridge.png left, "C·E·L Mathayom" center, ACT.png right) as a standalone template using locally-copied logo files. Direct `{% extends %}` from another repo is not used. |
| 2 | Does the report writer perform ERRANT analysis or does it render pre-existing results? | **Rendering only** — the report writer is a post-analysis presentation layer. The user provides already-analysed JSONs; no ingestion, correction, or ERRANT analysis is performed. | Feature summary updated. FR-013 scope refined: Pydantic validation is on pre-existing analysis JSONs only. The data scope is "all JSONs in the provided path" — no filtering, aggregation, or re-analysis. |
| 3 | Which LLM generates the report prose? | **The agent (Kilo) manages report writing itself** — the agent's own LLM capabilities generate all prose. No standalone Python→LLM calls for prose. Python/Jinja2/Playwright is used ONLY for HTML→PDF rendering. Tavily research is done via Kilo's builtin Tavily skill. | FR-008 updated: agent uses Tavily skill directly. FR-013 updated: agent delegates validation to a Python helper script. Success criterion for `response_format` reworded to agent-internal compliance. Feature summary updated to reflect agent-orchestrated workflow. |
| 4 | Is the Tavily API key currently configured in this project's `.env`? | **Yes, Tavily is configured** — confirmed by user. | FR-008 proceeds with Tavily search as specified. No fallback needed. |
| 5 | What institutional name and logo should appear in the report header? | **C·E·L Mathayom** — use the logos and heading from the existing report header in `C:\PROJECTS\WRITING_ASSESSMENT_NEW`. Logos must be copied into this project (not referenced externally). | FR-006: the Jinja2 header template must incorporate the C·E·L Mathayom masthead using locally-copied logo assets. |
