# Quickstart: Codebase Evaluation & Refactoring

## Prerequisites

```bash
# Python 3.14
python --version  # Must be 3.14.x

# Install production deps
pip install -r requirements.txt

# Install Playwright (new)
pip install playwright
playwright install chromium

# Install Pydantic (new)
pip install pydantic>=2.0

# Install Jinja2 (new)
pip install Jinja2

# Install pixelmatch for visual diff (new)
pip install pixelmatch

# Dev deps
pip install pytest pytest-cov pytest-mock

# spaCy model
python -m spacy download en_core_web_sm

# Lint
pip install ruff
```

## Verification Commands

```bash
# 1. Verify Python 3.14 and all deps import cleanly
python -c "import spacy; import errant; import playwright; import jinja2; import pydantic; print('All deps OK')"

# 2. Run existing test suite
pytest tests/ -v --tb=short

# 3. Check all 21 modules import
python -c "
import importlib, pkgutil
import src
modules = [name for _, name, _ in pkgutil.iter_modules(['src'])]
for m in sorted(modules):
    importlib.import_module(f'src.{m}')
    print(f'  ✓ {m}')
print(f'All {len(modules)} modules import OK')
"

# 4. Lint
ruff check src/ tests/

# 5. Run full test suite with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# 6. Verify no Typst dependency
python -c "import typst" 2>&1 | grep -q "ModuleNotFoundError" && echo "✓ Typst not importable"
```

## Test Scenarios

| Scenario | Command | Expected |
|----------|---------|----------|
| Smoke test all modules | `pytest tests/ -v --tb=short` | All tests pass or skip gracefully |
| Coverage check | `pytest --cov=src --cov-report=term` | >60% coverage on core modules |
| Playwright PDF generation | `python -c "from playwright.sync_api import sync_playwright; ..."` | PDF created |
| Jinja2 template renders | `python -c "from jinja2 import Environment; ..."` | HTML rendered |
| Pixel diff vs Typst | `pixelmatch baseline.png new.png diff.png` | <1% diff |
| Pipeline end-to-end | `python src/generate_report.py` (with test data) | PDF produced, no `typst compile` call |
| No response_format regression | `grep -r 'chat.completions.create' src/ | grep -v response_format` | Empty output |
| Config consolidation | `grep 'ERRANT_CODE_TO_COLUMN' src/*.py` | Single file match |

## Rollback Plan

1. `src/` directory is the single source of truth; keep `.bak` of changed files before refactoring
2. For Playwright→PDF migration: keep `generate_report.py` with both codepaths gated behind a `--engine typst|playwright` flag during transition
3. For `response_format` migration: each LLM call site is independent — no cross-script dependency
4. For Pydantic migration: old JSON files are still readable without validation — `model_validate` is additive, not breaking
