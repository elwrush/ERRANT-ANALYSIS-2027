# Skill: ingest-images

## Purpose

Transcribe handwritten student essays from scanned images into structured JSON using a vision language model (Gemini 2.5 Flash) via OpenRouter. Handles multi-page essays and rate-limited serial processing.

## Prerequisites

```bash
pip install -r requirements.txt
```

Set the API keys in `.env` or as environment variables:

```
OPENROUTER_API_KEY=sk-or-v1-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ESL_KEY=sb_secret_...
```

`SUPABASE_URL` and `SUPABASE_ESL_KEY` are optional — without them, student name/class lookup is skipped.

## Input Format

Place scanned images in subfolders of `inputs/`. Any JPEG or PNG filename is accepted. Images are **sorted by page number** (extracted from the last digit group in the filename), then **grouped sequentially** into chunks of `pages_per_essay`. The student ID is always extracted by the vision model from the page image content, never from the filename.

Examples with `pages_per_essay=2`:

```
img-0001.jpg, img-0002.jpg          → essay 1 (2 pages)
img-0003.jpg, img-0004.jpg          → essay 2 (2 pages)
```

Examples with `pages_per_essay=1`:

```
img-0001.jpg                        → essay 1 (1 page)
img-0002.jpg                        → essay 2 (1 page)
```

Files whose names don't contain a digit group for page numbering are treated as independent single-page essays with an auto-generated ID.

```
inputs/
  {folder_name}/
    any_images_here.jpg
```

## Usage

### Interactive mode (human at terminal)

```bash
python src/ingest.py
```

Shows a numbered menu of folders and prompts for pages per essay.

### CLI mode (for agents / automation)

```bash
python src/ingest.py --folder "M2-5A BASELINE" --pages 2
```

| Argument | Description |
|----------|-------------|
| `--folder` | Folder name (e.g. `"M2-5A BASELINE"`) or index number (e.g. `"2"`) |
| `--pages`  | Number of images per essay (e.g. `2`) |

Both arguments are optional. When omitted, the script falls back to interactive prompts.

### Workflow (agent mode)

Use the `question` tool to gather `--folder` and `--pages` from the user, then run the script with those arguments. The script processes each student's pages with jitter between requests and writes output JSONs to `outputs/{folder_name}/{student_id}.json`.

### ID verification sign-off (MANDATORY)

After ingestion completes, you **must** verify all extracted student IDs with the human before proceeding to any downstream step (ERRANT analysis, Supabase upload, report generation).

1. **Build the mapping** — After the script finishes, retrieve the `source_images` from each output JSON and the corresponding `student_id` to produce a complete image→ID map. Use:
   ```bash
   Get-ChildItem "outputs/{folder}/*.json" | ForEach-Object {
     $data = Get-Content $_ | ConvertFrom-Json
     "$($data.source_images[0]) -> $($data.student_id) ($($data.name))"
   }
   ```

2. **Highlight problems** — Identify any student IDs that are NOT in the Supabase classlist (those with empty `name` and `class` fields). Flag them as potential misreads.

3. **Present to user** — Use the `question` tool to show the full mapping and ask for confirmation or corrections. Example:
   ```
   Ingested 16 files from M2-4A BASELINE:
     img-0001.jpg → 30570 (Aton)
     img-0002.jpg → 36127 (Pang Pang)
     ...
     img-0005.jpg → 36717 (?? NOT in classlist)
     img-0009.jpg → 38995 (?? NOT in classlist)

   2 IDs not found in classlist (may be misreads or missing from roster):
     img-0005.jpg → 36717
     img-0009.jpg → 38995

   Do any IDs need correcting?
   ```

4. **Apply corrections** — If the user corrects an ID, update the ingestion JSON file immediately (rename file and fix `student_id`, `name`, `class` fields).

5. **Proceed only after sign-off** — Do not run ERRANT analysis, Supabase uploads, or report generation until the user has confirmed the IDs are correct.

### Preflight line-break check

After ingestion and ID sign-off, run the preflight check to catch artificial line breaks:
```bash
python src/preflight_check.py "FOLDER_NAME"
```
If any warnings appear (line break followed by lowercase = handwritten line wrap), fix the affected files before ERRANT analysis.

### Transcription rules (enforced by prompt)

- Verbatim — retain ALL errors (grammar, spelling, vocabulary)
- Student ID extracted from ID field on the page (not filename)
- Transcribe ONLY handwriting on ruled lines — skip the demographic header block (ID, class, name fields)
- `\n` ONLY at paragraph boundaries; never at fixed character widths
- Crossed-out text skipped; carat/insertion symbols resolved to natural flow

## Output Format

One JSON file per student. Multi-page essays have their pages joined with a single space.

```json
{
  "student_id": "12345",
  "student_text": "Page 1 content with \n paragraph breaks.\nPage 2 content...",
  "name": "August",
  "class": "M2-5A",
  "source_images": ["img-0001.jpg", "img-0002.jpg"]
}
```

| Field | Description |
|-------|-------------|
| `student_id` | 5-digit ID extracted from the page by the vision model |
| `student_text` | Transcribed text with `\n` at paragraph boundaries only |
| `name` | Student name from Supabase `classlists` table (empty if not found) |
| `class` | Sub-class label from Supabase `classlists` (e.g. M2-5A, empty if not found) |
| `source_images` | Original image filenames enabling cross-reference back to source scans |

### Supabase lookup

After extracting the student ID from the page, the script queries the Supabase `classlists` table for the student's `name` and `class`. If the student is not found (e.g. former students labelled M3), both fields are set to empty strings. This lookup requires `SUPABASE_URL` and `SUPABASE_ESL_KEY` environment variables — if either is missing, the lookup is skipped and both fields are empty.

## Model

| Config | Value |
|--------|-------|
| Provider | OpenRouter |
| Model | `google/gemini-2.5-flash` |
| Input price | $0.10 / 1M tokens |
| Output price | $0.40 / 1M tokens |
| Measured cost | ~$0.03 / 100 images (benchmark) |

## Image Preprocessing

| Parameter | Value |
|-----------|-------|
| Grayscale | Yes (`convert("L")`) |
| Max dimension | 1024px (LANCZOS) |
| JPEG quality | 90 |
| Approx tokens/image | ~576-676 |

## Transcription Rules (enforced by prompt)

- Transcribe verbatim — retain ALL spelling, grammar, and vocabulary errors
- Extract 5-digit student ID from the ID field on the page (not from filename)
- `\n` ONLY at paragraph boundaries — CRITICAL: never at handwritten line-wrap endings. Each paragraph flows as one continuous line. If a `\n` appears at every line ending, the transcription is WRONG.
- Never wrap lines at a fixed character width
- Crossed-out/deleted text is SKIPPED entirely
- Drawings, illustrations, doodles, emoji, and decorations (e.g. smiley faces, hearts, stars, apples, flowers) are SKIPPED entirely — they are not written text
- Carats (^) and insertion symbols: insert words at intended position for natural flow

## Page Joining

Multi-page essays are joined with a single space (`" "`) between pages, never with `\n`. This ensures that a paragraph running continuously across pages does not get an artificial line break. Additionally, single `\n` within each page's transcription are collapsed to spaces in post-processing — double `\n\n` (paragraph breaks) are preserved. The model is unreliable at distinguishing handwritten line wraps from paragraph breaks.

## Rate Limiting

- **Jitter**: 0.5–2.0s random delay between every API request
- **Backoff**: exponential (2^n + random) on 429/502/503, up to 5 retries
- **Timeout**: 30s per request
- **Concurrency**: serial (one request at a time)

## Pipeline handoff

After the user signs off on the IDs, the pipeline proceeds to ERRANT analysis.
Do **not** skip the ID verification step — misread student IDs are the most common source of downstream errors.
