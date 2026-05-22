# Skill: ingest-images

## Purpose

Transcribe handwritten student essays from scanned images into structured JSON using a vision language model (Gemini 2.5 Flash Lite Preview) via OpenRouter. Handles multi-page essays and rate-limited serial processing.

## Prerequisites

```bash
pip install -r requirements.txt
```

Set the API key in `.env` or as an environment variable:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

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

```bash
python src/ingest.py
```

The script is fully interactive — once launched it handles all prompts directly:
1. Scans `inputs/` for subfolders and shows a numbered list — user types the number to select a folder
2. Asks for pages per essay — user types a numeral (e.g. `1`, `2`, `3`, `4`)
3. Images are sorted by page number and grouped sequentially into essays of `N` pages each (where `N` is the number you entered). Images without a page-number digit group become single-page essays with auto-generated IDs. Pages within an essay are joined with a single space (not `\n`) so continuous paragraphs flow correctly.
4. Processes each student's pages serially with jitter between requests
5. Writes output JSONs to `outputs/{folder_name}/{student_id}.json`

## Output Format

One JSON file per student. Multi-page essays have their text joined with `\n`.

```json
{
  "student_id": "12345",
  "student_text": "Page 1 content with \n paragraph breaks.\nPage 2 content...",
  "source_images": ["img-0001.jpg", "img-0002.jpg"]
}
```

The `source_images` field lists the original image filenames that produced the transcription, enabling cross-reference back to the source scans.

## Model

| Config | Value |
|--------|-------|
| Provider | OpenRouter |
| Model | `google/gemini-2.5-flash-lite-preview-09-2025` |
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

Multi-page essays are joined with a single space (`" "`) between pages, never with `\n`. This ensures that a paragraph running continuously across pages does not get an artificial line break. Additionally, all `\n` within each page's transcription are collapsed to spaces in post-processing — the model is unreliable at distinguishing handwritten line wraps from paragraph breaks, so paragraph structure is determined solely by the page joining logic.

## Rate Limiting

- **Jitter**: 0.5–2.0s random delay between every API request
- **Backoff**: exponential (2^n + random) on 429/502/503, up to 5 retries
- **Timeout**: 30s per request
- **Concurrency**: serial (one request at a time)
