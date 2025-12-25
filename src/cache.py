from functools import wraps
import hashlib
from datetime import datetime, timedelta


class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str, ttl_seconds: int = 3600):
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=ttl_seconds):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value):
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

    def clear(self):
        self.cache.clear()
        self.timestamps.clear()


cache = SimpleCache()


def cache_result(ttl_seconds: int = 300):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_raw = f"{func.__name__}:{(args, kwargs)}"
            key = hashlib.md5(key_raw.encode()).hexdigest()

            cached = cache.get(key, ttl_seconds)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator
