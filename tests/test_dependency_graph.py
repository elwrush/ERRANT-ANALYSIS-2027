import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDependencyGraph:
    def test_pydeps_analyzes_modules(self):
        result = subprocess.run(
            [sys.executable, "-m", "pydeps", "src", "--only", "src", "--max-bacon", "3", "--no-output"],
            cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"pydeps failed: {(result.stderr or result.stdout)[:500]}"

    def test_no_circular_dependencies(self):
        result = subprocess.run(
            [sys.executable, "-m", "pydeps", "src", "--only", "src", "--show-cycles", "--no-output"],
            cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=30,
        )
        cycles_stderr = (result.stderr or "").lower()
        cycles_stdout = (result.stdout or "").lower()
        has_cycles = "cycle" in cycles_stderr or "cycle" in cycles_stdout
        if has_cycles:
            assert False, f"Circular dependencies detected:\n{result.stderr}\n{result.stdout}"
