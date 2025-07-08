#!/usr/bin/env python3
"""
This module provides a `get_page` function that fetches a URL,
caches the result in Redis for 10 seconds, and counts how many
times each URL has been accessed.
"""

import redis
import requests
from functools import wraps
from typing import Callable

# Connect to local Redis server
r = redis.Redis()


def count_and_cache(fn: Callable) -> Callable:
    """
    Decorator to count accesses to a URL and cache the result in Redis
    for 10 seconds. Uses the URL as key.
    """

    @wraps(fn)
    def wrapper(url: str) -> str:
        cache_key = f"cache:{url}"
        count_key = f"count:{url}"

        # Check Redis cache first
        cached = r.get(cache_key)
        if cached:
            return cached.decode("utf-8")

        # Increment access counter
        r.incr(count_key)

        # Fetch from the web
        result = fn(url)

        # Cache result with 10-second expiration
        r.setex(cache_key, 10, result)
        return result

    return wrapper


@count_and_cache
def get_page(url: str) -> str:
    """
    Fetches the HTML content of a URL using requests.
    If cached, returns cached version (via decorator).
    """
    response = requests.get(url)
    return response.text
