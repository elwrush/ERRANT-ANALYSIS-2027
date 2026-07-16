# Contract C-002: Data Aggregation

## Function Signature

```python
def aggregate_data(valid_files: list[Path]) -> AggregatedReportData:
    """
    Compute aggregated statistics from validated ERRANT analysis JSONs.

    Args:
        valid_files: List of paths to validated ErrantOutput JSONs.

    Returns:
        AggregatedReportData with per-student, per-code, per-cohort stats.

    Raises:
        ValueError: If valid_files is empty.
    """
```

## Output Schema

See `data-model.md` for full schema. Key output contracts:

```python
class AggregatedReportData(BaseModel):
    meta: ReportMeta
    students: list[StudentSummary]
    error_code_summary: list[ErrorCodeBucket]
    cohort_summary: list[CohortBucket]
    overall_stats: OverallStats
    charts: list[ChartRef]
```

## Edge Case Handling

| Condition | Behaviour |
|-----------|-----------|
| All students from same cohort | `cohort_summary` has 1 entry; `meta.cohorts` has 1 value |
| No errors in any student | `error_code_summary` is empty; `overall_stats.mean_error_rate` is 0 |
| Student with word_count < 40 | Included in `students`, `error_rate` is None, flagged in note |
| Mixed B1/B2 students | `cefr_level` inferred from `class_` prefix; counts in `overall_stats` |
| Single student | `cohort_summary` computed but charts switch to table format |
| 50+ students | All statistics computed normally; histogram chart generated if n ≥ 10 |
