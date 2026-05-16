import time
import random
from functools import wraps


class RetryableError(Exception):
    pass


class NonRetryableError(Exception):
    pass


def retry(max_retries=3, max_delay=60, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except NonRetryableError as e:
                    print(f"  Non-retryable error: {e}")
                    return None
                except RetryableError as e:
                    if attempt < max_retries:
                        delay = min((base_delay * 2 ** attempt) + random.uniform(0, 1), max_delay)
                        print(f"  Retrying in {delay:.1f}s...  (attempt {attempt + 1}/{max_retries}, {e})")
                        time.sleep(delay)
                    else:
                        print(f"  Failed after {max_retries} retries: {e}")
                        return None
        return wrapper
    return decorator
