import time
import random
from functools import wraps


class RetryableError(Exception):
    pass


def retry(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    if attempt < max_retries:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        print(f"  Retrying in {delay:.1f}s...  ({e})")
                        time.sleep(delay)
                    else:
                        print(f"  Failed after {max_retries} retries: {e}")
                        return None
        return wrapper
    return decorator
