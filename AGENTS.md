# AGENTS.md — ERRANT-ANALYSIS

Pipeline: scanned essays → `outputs/{folder}/{id}.json` (OCR) → preflight line-break check → ERRANT analysis → `local-working/` → per-student PDFs (`PDF/{folder}/`) + main report PDF.

**Authoritative workflows live in skills — read them first:** `.opencode/skills/errant-analysis/SKILL.md` (analysis + Supabase), `.opencode/skills/ingest-images/SKILL.md` (OCR), `.opencode/skills/local-report/SKILL.md` (per-student PDFs), `.opencode/skills/rename-json-files/SKILL.md` (filename normalisation), `.opencode/command/write-technical-report.md` (main report). Trigger via `/errant-analysis`, `/ingest-images`, `/local-report`, `/rename-json-files`, `/write-technical-report`.

**Architecture decisions:** see `adr/` (index at `adr/README.md`) before changing a subsystem.

## Commands (in order)

```bash
# 1. OCR scanned images -> outputs/{folder}/{id}.json  (ask the user for --pages first)
python src/ingest.py --folder "M2-3B" --pages 1

# 2. Preflight: flag artificial line breaks (lowercase continuations). Fix by hand — there is no --fix flag.
python src/preflight_check.py "M2-3B"

# 3. ERRANT analysis (DeepSeek correction + ERRANT + LLM summaries); auto-runs step 4 at the end.
#    Ghost gate: exits 1 if outputs/{folder}/GHOST_REPORT.txt exists.
python src/errant_analysis.py --batch "M2-3B"          # analysis only
python src/errant_analysis.py --batch "M2-3B" --insert # ALSO insert to Supabase error_reports (gated)

# 4. Per-student PDFs (standalone refresh; charts come from Supabase)
python src/generate_report.py "M2-3B"

# 5. Main cohort report (subcommands: validate | aggregate | charts | render)
python src/technical_report_writer.py render <draft.md> <output.pdf>
```

Run from the repo root — step 3 shells out to `src/generate_report.py` via a relative path.

## Verification

- `ruff check src/ tests/` — clean.
- `pytest tests/ -v` — **246 pass, 4 fail on a clean tree.** The 4 are stale tests vs. current APIs, *not* caused by your change: `test_report.py::TestRenderReport::test_esc_handles_special_chars` (imports removed `esc`), and `test_technical_report_writer.py::{TestRenderTechnicalReport::test_missing_template_raises, TestCLI::test_render_subcommand_missing_draft, TestCitationAnnotation::test_citation_map_generated}` (`render_technical_report()` signature drift; `test_citation_map_generated` has a stray appended PIL/SVG grayscale block). Note `TestGenerateCharts::test_charts_grayscale` was fixed in spec 003 and now passes.
- `tests/test_dependency_graph.py` shells out to `python -m pydeps`; **`pydeps` is not in `requirements.txt`** — install it separately or those two tests error.
- Plain `requirements.txt`; no Makefile / pyproject / justfile / Taskfile.

## Hard-won gotchas

- **`student_id` must be exactly 5 digits** — `IngestionOutput` / `ErrantOutput` / `ReportData` reject anything else (`src/models.py`). Classes with no Supabase `classlists` entry need placeholder IDs in a non-colliding 5-digit range (e.g. `90001+`; real IDs are 29xxx–37xxx). Non-5-digit IDs (`01`, `13`) fail validation silently.
- **`preflight_check.py` prints "Run with --fix to auto-repair" but no such flag exists** (line 53). Fix flagged `\n` continuations manually (join the line into the previous paragraph).
- **Ghost gate ≠ missing-student warning.** `GHOST_REPORT.txt` hard-blocks the batch (fix IDs, delete file). Missing-from-classlist is only a warning logged to `local-working/missing_student_ids.txt` — the batch proceeds using `name`/`class` from the input JSON.
- **`generate_report.py` folder filter is strict.** It matches filename stems with `^{folder}-[^-]+$`, so the folder name must match exactly and the record id must be a single hyphen-free segment. Files like `M3-4A-assignment-2-29561.json` are **silently skipped**. With no folder argument it processes **all** of `local-working/`.
- **`technical_report_writer.py render` aggregates ALL of `local-working/`** (`src/technical_report_writer.py:691`), not a folder filter. For a single-class report, build a filtered dataset like `scripts/render_m2_3b_report.py` does (globs `M2-3B-9*.json`).
- **`templates/tech_report.html` is hard-coded** for the M2/M3 comparison report and **ignores draft sections** — only the `## References` fenced JSON block is parsed. Draft content reaches the PDF only via a section-driven template that loops `context.sections` (e.g. `templates/m2_3b_report.html` + `scripts/render_m2_3b_report.py`). Pipe tables need `MarkdownIt("commonmark").enable("table")` (`src/technical_report_writer.py:424`).
- **`generate_report.py` writes one standalone PDF per student** (`PDF/{folder}/{dd-mm-yy}-{HHMM}-{class}-{sid}.pdf`) — there is no merge, no 4-page padding, no interleaving, and no combined `*-errant-report.pdf`. Transparency is removed at the source (logos composited to opaque RGB PNGs via `src/image_utils.py`; charts are alpha-free SVG), so **Ghostscript is no longer used** by either report pipeline. Legacy merged/flattened PDFs already in `PDF/` are left untouched.
- **Supabase writes are gated**: `--insert` (`errant_analysis.py`), `--upsert` (`batch_errant_upsert.py`). Never write without explicit user request. `insert_error_reports()` dedupes on `(student_id, date)` and re-queries to verify.
- **Env**: `DEEPSEEK_API_KEY` lives in the zsh env (`~/.env`), **not** the project `.env` (which has `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ESL_KEY`). `errant_analysis.py` calls `load_dotenv(override=True)`. Also needed: `OPENROUTER_API_KEY` (ingest), `SUPABASE_ACCESS_TOKEN` (DDL).
- **SQL**: ad-hoc reads via `supabase db query --linked "..."`; DDL via `python src/supabase_sql.py "SQL"` (never psycopg2 for migrations).
- **`error_percent` is an INTEGER column** — cast `::numeric` for `ROUND`/`STDDEV` in SQL. Word count < 40 → `error_percent NULL` (policy in both `errant_analysis.py` and `batch_errant_upsert.py`).
- **Two benchmark systems — don't conflate.** `config.py` `B1_TARGET=15`, `B2_TARGET=10` are aspirational classroom targets used in per-student PDF charts. Main reports cite empirical CEFR rates from Štulrajterová (2023): B1 ~19%, B2 ~15% (manual Louvain annotation; not directly comparable to ERRANT).
- **Fluency-rewrite guard**: corrections are retried (max 3) if `len(corrected)/len(original) > 1.3`, edits/word > 1.0, or sentence-count ratio > 2.0 (`is_fluency_rewrite`).
- **Images/charts in PDFs**: `generate_report.py` embeds SVG charts + masthead logos as base64 data URIs via `_file_to_data_uri()` — Playwright `set_content()` can't load bare POSIX/`file://` paths.
- **Automation**: `.github/workflows/daily-supabase-backup.yml` dumps Supabase roles/schema/data to `backups/` daily (02:00 UTC) and auto-commits. Expect bot commits; don't hand-edit `backups/`.

## Data sources

- `local-working/{folder}-{id}.json` — per-student pipeline output: `original_text`, `corrected_text`, `corrected_typst` (HTML with `<u>`/`<br>`), `errant_analysis.errors[]` (type/example/context/count), `sentence_pairs[]`, `summary` + `summary_type` (`"llm"` or `"empty"`; no deterministic fallback), `error_rate`, `word_count`, `date_created` (written to the `date` column on insert).
- Supabase `error_reports` — full historical corpus: 45 ERRANT-code columns (`ERRANT_CODE_TO_COLUMN` in `src/config.py`) + `date` + `academic_year`.
- `outputs/drafts/` — report Markdown drafts with a trailing `## References` fenced JSON block (APA 7th, `formatted` field; templates render `{{ ref.formatted | safe }}`).
