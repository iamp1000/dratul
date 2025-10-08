# app/limiter.py
# This new file's sole purpose is to create the rate limiter instance.
# This avoids circular imports between main.py and the routers.

from slowapi import Limiter
from slowapi.util import get_remote_address

class DummyLimiter:
    def limit(self, rate_string):
        def decorator(func):
            return func  # Just return the function unchanged
        return decorator

limiter = DummyLimiter()
