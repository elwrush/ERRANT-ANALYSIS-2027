# Dependency Graph Analysis

Generated: 2026-07-13 via `pydeps src --only src --max-bacon 3`

## Graph

![Dependency graph](dependency_graph.svg)

## Module Inventory (15 kept, 6 archived)

| Module | Dependencies | Consumers |
|--------|-------------|-----------|
| `config.py` | None (stdlib only) | All pipeline modules |
| `models.py` | pydantic | errant_analysis.py, ingest.py, generate_report.py |
| `_retry.py` | None | errant_analysis.py, ingest.py |
| `ingest.py` | config, models, _retry, PIL, requests | errant_analysis.py |
| `errant_analysis.py` | config, models, _retry, generate_report (esc), spacy, errant, openai | batch_errant_upsert.py |
| `generate_report.py` | config, models, jinja2, playwright, matplotlib | (leaf) |
| `batch_errant_upsert.py` | config, errant_analysis | (standalone) |
| `migrate_writing_records.py` | supabase | (standalone) |
| `rename_json_files.py` | config, supabase | (standalone) |
| `preflight_check.py` | None (standalone) | (standalone) |
| `research_prep.py` | supabase | (standalone) |
| `interpret_results.py` | pandas, supabase | (standalone) |
| `desk_statistics.py` | pandas, scipy, matplotlib | (standalone) |
| `sampling_strategy.py` | supabase | (standalone) |
| `setup_error_analysis.py` | supabase_sql | (standalone) |
| `supabase_sql.py` | requests | (standalone) |

## Circular Dependency Check

**Result: No circular dependencies found.** All imports follow a clean DAG:

```
config.py ──→ ingest.py ──→ errant_analysis.py ──→ generate_report.py
    │            │                │                      │
    │            │                ├── batch_errant_upsert │
    │            │                │                      │
    └────────────┴────────────────┴──────────────────────┘
         (config consumed by all pipeline modules)
```

## Maximum Import Depth

config.py → errant_analysis.py → generate_report.py: **2 levels** (satisfies <3 threshold).

## Archived Modules (6)

Moved to `scripts/archive/`: pilot_prep.py, query_class_mapping.py, query_skill_count.py, write_historical_data.py, test_models.py, add_word_count.py.
