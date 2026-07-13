import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.chdir(Path(__file__).resolve().parent.parent)

from _retry import RetryableError, NonRetryableError, retry


class TestRetryDecorator:
    def test_retryable_error_retries(self):
        call_count = 0

        @retry(max_retries=2)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("not yet")
            return "success"

        result = flaky()
        assert result == "success"
        assert call_count == 2

    def test_non_retryable_passthrough(self):
        @retry(max_retries=2)
        def fatal():
            raise NonRetryableError("fatal")

        result = fatal()
        assert result is None

    def test_max_retries_exceeded(self):
        call_count = 0

        @retry(max_retries=2)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise RetryableError("always")

        result = always_fails()
        assert result is None
        assert call_count == 3  # initial + 2 retries

    def test_non_error_return(self):
        @retry(max_retries=2)
        def ok():
            return 42

        assert ok() == 42
