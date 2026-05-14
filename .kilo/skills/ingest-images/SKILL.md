# Skill: ingest-images

## Purpose

Transcribe handwritten student essays from scanned images into structured JSON using a vision language model (Gemini 2.5 Flash Lite Preview) via OpenRouter. Handles multi-page essays, prompt caching, and rate-limited serial processing.

## Prerequisites

```bash
pip install -r requirements.txt
```

Set the API key in `.env` or as an environment variable:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

## Input Format

Images live in subfolders of `inputs/`. Naming convention:

```
inputs/
  {folder_name}/
    {student_id}_{page_num}.jpg
```

Example — a 2-page essay by student 12345 and a 1-page essay by student 67890:

```
inputs/class_a/12345_1.jpg
inputs/class_a/12345_2.jpg
inputs/class_a/67890_1.jpg
```

## Usage

```bash
python src/ingest.py
```

The script is interactive. It will:
1. Scan `inputs/` for subfolders and show an enumerated list
2. Ask you to pick one
3. Ask how many image pages per essay (determines grouping)
4. Process each student's pages serially with jitter between requests
5. Write output JSONs to `outputs/{folder_name}/{student_id}.json`

## Output Format

One JSON file per student. Multi-page essays have their text joined with `<br>`.

```json
{
  "student_id": "12345",
  "student_text": "Page 1 content with <br> paragraph breaks.<br>Page 2 content..."
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
| Prompt caching | Automatic (OpenRouter sticky routing) |

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
- Paragraph breaks rendered as `<br>`; blank lines as `<br><br>`
- No artificial line breaks within paragraphs
- Crossed-out/deleted text is SKIPPED entirely
- Carats (^) and insertion symbols: insert words at intended position for natural flow

## Rate Limiting

- **Jitter**: 0.5–2.0s random delay between every API request
- **Backoff**: exponential (2^n + random) on 429/502/503, up to 5 retries
- **Timeout**: 30s per request
- **Concurrency**: serial (one request at a time)
