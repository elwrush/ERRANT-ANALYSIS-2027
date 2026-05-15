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

Place scanned images in subfolders of `inputs/`. Any JPEG or PNG filename is accepted — the script attempts to extract student ID and page number from filenames matching `{student_id}_{page_num}` for multi-page grouping. Files with unrecognizable names are treated as independent single-page essays with an auto-generated ID.

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
3. Images named `{student_id}_{page_num}` are grouped automatically by student; unrecognized filenames become single-page essays with auto-generated IDs. Paragraphs are separated by `\n` in the output
4. Processes each student's pages serially with jitter between requests
5. Writes output JSONs to `outputs/{folder_name}/{student_id}.json`

## Output Format

One JSON file per student. Multi-page essays have their text joined with `\n`.

```json
{
  "student_id": "12345",
  "student_text": "Page 1 content with \n paragraph breaks.\nPage 2 content..."
}
```

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
- `\n` ONLY at actual paragraph boundaries — never for line wrapping
- Never wrap at a fixed character width; each paragraph flows as one continuous line
- Crossed-out/deleted text is SKIPPED entirely
- Carats (^) and insertion symbols: insert words at intended position for natural flow

## Rate Limiting

- **Jitter**: 0.5–2.0s random delay between every API request
- **Backoff**: exponential (2^n + random) on 429/502/503, up to 5 retries
- **Timeout**: 30s per request
- **Concurrency**: serial (one request at a time)
