# Contract C-003: Chart Generation

## Function Signature

```python
def generate_charts(data: AggregatedReportData, output_dir: Path) -> list[ChartRef]:
    """
    Generate grayscale-safe charts from aggregated data.

    All charts use hatching/patterns (not color) for differentiation.
    All charts are saved as PNG at 150 DPI.

    Args:
        data: Aggregated report data.
        output_dir: Directory to save chart images.

    Returns:
        List of ChartRef with paths and metadata.

    Raises:
        FileNotFoundError: If output_dir cannot be created.
    """
```

## Chart Types

### Chart 1: ERRANT Code Frequency (horizontal bar)
- X-axis: error count
- Y-axis: ERRANT supercategory (R, M, U) + top 10 specific codes
- Hatching: solid for R, `//` for M, `..` for U
- Grayscale fill: 30% gray for R, 50% for M, 70% for U
- Output: `<output_dir>/charts/errant-code-frequency.png`

### Chart 2: Cohort Comparison (grouped bar)
- X-axis: ERRANT supercategory
- Groups: one bar per cohort
- Hatching: solid for first cohort, `//` for second, `x` for third
- Output: `<output_dir>/charts/cohort-comparison.png`
- Note: If only 1 cohort or n < 2 per cohort, skip chart, provide table instead

### Chart 3: Error Rate Distribution (histogram)
- X-axis: error rate buckets (0–5, 5–10, 10–15, etc.)
- Y-axis: number of students
- Single gray fill with `|` hatching
- Output: `<output_dir>/charts/error-rate-distribution.png`
- Condition: Only generated if n ≥ 10 students

### Chart 4: Per-Student Trend (line chart, optional)
- Per-student error rate over submission dates
- Only for students with ≥2 historical data points
- Output: `<output_dir>/charts/trend-<student_id>.png`
- Solid line, circular markers, gray scale

## Grayscale Rules

| Element | Rule |
|---------|------|
| Bar fill | `color='black', alpha=0.15–0.35` |
| Hatch patterns | `hatch='//'`, `hatch='..'`, `hatch='x'`, `hatch='|'` |
| Lines | `color='#333333'`, `linewidth=1.5` |
| Grid | `color='#cccccc'`, `linewidth=0.5` |
| Text | `color='black'` |
| Axes | `spines['top'].set_visible(False)`, `spines['right'].set_visible(False)` |
| Font | `fontsize=9` labels, `fontsize=8` ticks |

## Contract Tests

| Test | Input | Expected |
|------|-------|----------|
| Normal data (3 cohorts, 30 students) | AggregatedReportData with 3 cohorts | 4 chart files created |
| Single cohort | AggregatedReportData with 1 cohort | 3 chart files (no cohort comparison) |
| Few students (n=3) | AggregatedReportData with 3 students | 2 chart files (no histogram) |
| All charts grayscale | Any AggregatedReportData | All chart images pixel-checked: no color pixels (RGB channels equal) |
