# Contract C-005: Citation Management — Source PDF Annotation & Citation Map

## Function Signatures

```python
def annotate_source_pdf(
    source_path: Path,
    citations: list[CitationSpan],
    output_dir: Path,
) -> Path | None:
    """
    Annotate a source PDF with highlights and sticky notes for cited passages.

    Opens the PDF with PyMuPDF (fitz), locates each cited text span on its
    page, adds a yellow highlight, and attaches a sticky annotation containing
    the report section name.

    Args:
        source_path: Path to the source PDF.
        citations: List of CitationSpan objects (page, text, section).
        output_dir: Directory to save annotated PDF.

    Returns:
        Path to annotated PDF, or None if annotation was skipped
        (scanned/no-text, encrypted, missing).

    Raises:
        FileNotFoundError: If source_path does not exist.
    """


def generate_citation_map(
    citations_by_section: dict[str, list[tuple[str, str, int, str]]],
    annotated_dir: Path,
    output_path: Path,
) -> Path:
    """
    Generate a Markdown citation map from all inline citations in the draft.

    Args:
        citations_by_section: Map of section_name → list of
            (citation_text, source_file, page_num, quoted_passage).
        annotated_dir: Directory containing annotated PDFs.
        output_path: Path to write the citation map Markdown file.

    Returns:
        Path to the written citation-map.md.
    """
```

## Input Schemas

```python
class CitationSpan(BaseModel):
    source_path: Path
    page: int
    text: str                    # The exact text span to highlight
    section: str                 # Report section that cites this
    citation_text: str           # Full inline citation e.g. "(Ellis, 2008, p. 72)"

class CitationMapEntry(BaseModel):
    citation_text: str
    source_file: str             # Filename in annotated/ dir
    page: int
    quoted_passage: str          # The exact highlighted text
```

## Annotated PDF Contract

| Requirement | Implementation |
|-------------|---------------|
| Highlight colour | Yellow (`(1, 1, 0)`) — visible in grayscale as light gray |
| Sticky annotation text | `"Cited in: <section name>"` |
| Annotation type | `fitz.annot.Text` with icon "Note" |
| Output filename | `<source-stem>-annotated.pdf` |
| Output directory | `references/annotated/` (created if missing) |

## Citation Map Format

The `citation-map.md` uses per-section headings with bullet entries:

```markdown
# Citation Map — <Report Title>

## Section: Introduction
- (Ellis, 2008, p. 72) → `references/annotated/Ellis-2008-annotated.pdf`, page 72
  > "Explicit instruction on grammatical structures leads to significant improvement in accuracy for adolescent L2 learners"

## Section: What does this report say about our students' proficiency?
- (Lightbown & Spada, 2013, p. 45) → `references/annotated/Lightbown-Spada-2013-annotated.pdf`, page 45
  > "Learners in foreign language settings often have limited exposure to the target language outside the classroom"
```

## Edge Cases

| Condition | Behaviour |
|-----------|-----------|
| Source PDF missing | Log warning, `annotate_source_pdf()` returns None, citation map entry says "Source not available for annotation" |
| Scanned PDF (no text layer) | `page.get_text()` returns empty → log warning, return None, citation map entry says "Scanned PDF — no text layer for annotation" |
| Encrypted PDF | `fitz.open()` raises `FileDataError` → catch, log warning, return None, citation map entry says "Permission-protected — could not annotate" |
| Text span not found on page | Log warning, highlight entire page as fallback with annotation "Approximate location — exact text not found" |
| Multiple citations from same source | Annotate all spans in one pass, save one annotated PDF per source |

## Contract Tests

| Test | Input | Expected |
|------|-------|----------|
| Valid PDF with text | PDF with known text, CitationSpan matching text on page | Highlight and sticky annotation present; output PDF saved |
| Multiple citations one source | 3 CitationSpans from same PDF | Single annotated PDF with 3 highlights |
| Missing source file | Non-existent Path | Returns None, no crash |
| Scanned (no-text) PDF | Image-only PDF | Returns None, no crash |
| Citation map generation | Map of 2 sections × 2 citations each | Markdown file with 2 `## Section` headings, 4 bullet entries, each with `>` quoted passage |
