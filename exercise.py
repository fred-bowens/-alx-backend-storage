#!/usr/bin/env python3
"""This module defines a Cache class that stores data in Redis and tracks method history."""

import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called using Redis.

    Key format: <qualified_name>
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator to store the history of inputs and outputs for a method in Redis.

    Keys:
      - <qualified_name>:inputs
      - <qualified_name>:outputs
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result
    return wrapper


def replay(method: Callable) -> None:
    """
    Display the call history of a given method.

    Output format:
        Method was called N times:
        <qualified_name>(*args) -> result
    """
    redis_client = method.__self__._redis
    name = method.__qualname__
    inputs = redis_client.lrange(f"{name}:inputs", 0, -1)
    outputs = redis_client.lrange(f"{name}:outputs", 0, -1)

    print(f"{name} was called {len(inputs)} times:")
    for inp, out in zip(inputs, outputs):
        print(f"{name}(*{inp.decode('utf-8')}) -> {out.decode('utf-8')}")


class Cache:
    """
    Cache class for storing and retrieving values in Redis.

    It includes:
    - call tracking
    - input/output history
    - type-safe get methods
    """

    def __init__(self):
        """Initialize Redis and flush any existing data."""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store the provided data in Redis under a UUID key.

        Args:
            data: The data to store.

        Returns:
            The generated key as a string.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieve data from Redis by key and optionally apply a transformation function.

        Args:
            key: Redis key to fetch.
            fn: Optional callable to convert the result.

        Returns:
            Retrieved and transformed data or None.
        """
        data = self._redis.get(key)
        if data is None:
            return None
        return fn(data) if fn else data

    def get_str(self, key: str) -> Optional[str]:
        """Retrieve a value from Redis as a UTF-8 string."""
        return self.get(key, fn=lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> Optional[int]:
        """Retrieve a value from Redis and cast it to int."""
        return self.get(key, fn=int)
