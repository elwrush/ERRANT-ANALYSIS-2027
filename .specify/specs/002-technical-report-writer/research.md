# Research Findings — Technical Report Writer

## 1. Input JSON Schema

### ErrantOutput (existing at `src/models.py:63`)
- `student_id`: str (5-digit)
- `original_text`: str (non-empty)
- `corrected_text`: str (non-empty)
- `sentence_pairs`: list[dict]
- `corrected_typst`: str
- `error_rate`: int | None (0–100)
- `word_count`: int
- `name`: str
- `class_`: str (alias "class")
- `record_id`: str
- `submission_date`: str
- `topic`: str
- `summary`: str
- `summary_data`: dict | None
- `summary_type`: str
- `date_created`: str
- `metadata`: Metadata
- `errant_analysis`: ErrantAnalysis (errors list, uncategorised list, dropped_edits dict)

**Key insight**: `errant_analysis.errors` contains individual error objects with their ERRANT codes. No `cohort` field exists in the schema — cohort would need to be derived from `class_` (M2/M3 prefix).

### ERRANT Error Objects
Each error in `errant_analysis.errors` has:
- `error_code`: str (e.g. "R:VERB:TENSE")
- `error_type`: str
- `severity`: str
- `cefr_level`: str
- `message`: str
- `correction`: str
- `original`: str

## 2. Chart Library Compatibility

### Matplotlib (Agg backend)
- Already installed and working (`generate_chart()` in `generate_report.py`)
- **Grayscale-safe hatch patterns available**: `['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']`
- **Usage**: `ax.bar(..., hatch='//')` — crosshatching is the most grayscale-discernible pattern
- **Recommendation**: Use distinct hatching for each cohort/group. Pair with different gray fill levels (30%, 50%, 70% black) for additional discrimination.
- **Dots and stripes**: Use `hatch='.'` for dot pattern, `hatch='/'` for diagonal, `hatch='x'` for crosshatch

### Alternatives considered
- **Seaborn**: Overkill for this use case. Adds dependency without benefit since we only need bar charts.
- **Plotly**: Interactive — unnecessary for static PDF output. Heavy dependency.
- **Vega-Lite**: Would require JavaScript rendering — adds complexity to the Jinja2→Playwright pipeline.
- **Conclusion**: Matplotlib is the right choice. Already in project deps.

## 3. Playwright Capabilities

### CSS Paged Media
- `@page { size: A4; margin: 1.6cm; }` — fully supported
- `page-break-before: always` — supported
- `page-break-after: avoid` — partially supported
- Print media emulation: `page.emulate_media(media="print")`

### Image embedding
- Local file paths work with Playwright when using `src="images/file.png"` if the HTML file is served or the path is absolute
- **Recommendation**: Use `file://` absolute paths for chart images, or embed as base64 data URIs for portability

### Font support
- Roboto family available via TinyTeX (as per AGENTS.md)
- Fallback: system sans-serif
- Recommend explicit `@font-face` or system font declaration in template CSS

## 4. Grayscale Charting Best Practice

| Pattern | Hatch code | Visual discrimination | Recommendation |
|---------|-----------|----------------------|----------------|
| Solid | (none) | High | Use for primary data series |
| Crosshatch | `//` | Very high | Use for first comparison group |
| Dots | `..` | Medium | Use for second comparison group |
| Diagonal | `\\` | High | Use for third comparison group |
| Vertical stripes | `|` | Medium | Use for fourth comparison group |
| Cross | `x` | High | Use for fifth comparison group |

**Pair with fill alpha**: Combine hatch with `color='black'` and `alpha=0.1–0.3` fill for best results.

## 5. Tavily Rhetorical Research

- Tavily API key confirmed configured
- Search queries to use:
  1. "professional technical report writing style guide rules"
  2. "how to avoid AI slop in academic writing"
  3. "Australian academic writing conventions grammar"
  4. "teacher report writing best practices ESL"
  5. "principles of clear data-driven writing"
- Results are compiled into inline style rules applied by the agent during prose composition

## 6. Reference Citation Format

- All references must use APA 7th edition in-text and reference list
- In-text: `(Author, 2020, p. 42)` or `Author (2020, para. 4)`
- Reference list: `Author, A. A. (2020). *Title of work*. Publisher. DOI`
- The agent must include page/paragraph numbers for EVERY citation

## 7. ERRANT Code Categories (from config.py)

43 codes grouped by supercategory:
- **R** (Replacement): NOUN, VERB, ADJ, ADV, PREP, PRON, DET, CONJ, PART, PUNCT, SPELL, ORTH, MORPH, WO, CONTR
- **M** (Missing): NOUN, VERB, PREP, PRON, DET, CONJ, PART, PUNCT
- **U** (Unnecessary): NOUN, VERB, PREP, PRON, DET, CONJ, PART, PUNCT
- **OTHER**, **UNK**

Supercategory aggregation is the primary reporting axis; individual codes are secondary.
