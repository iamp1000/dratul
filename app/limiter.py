# app/limiter.py
# This new file's sole purpose is to create the rate limiter instance.
# This avoids circular imports between main.py and the routers.

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
