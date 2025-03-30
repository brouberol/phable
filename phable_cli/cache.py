import inspect
import json
import os
import sys
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

CACHE_HOME_PER_PLATFORM = {
    "darwin": Path.home() / "Library" / "Caches",
    "linux": Path(os.getenv("XDG_CACHE_HOME", f"{Path.home()}/.config")),
    "windows": Path("c:/", "Users", os.getlogin(), "AppData", "Local", "Temp"),
}


class Cache:
    """A persistent cache for long-lived data, such as user or project"""

    def __init__(self):
        self.cache_dir = CACHE_HOME_PER_PLATFORM[sys.platform] / "phind"
        if not self.cache_dir.exists():
            self.cache_dir.mkdir()
        self.cache_filepath = self.cache_dir / "cache.json"
        if self.cache_filepath.exists():
            self.data = json.load(open(self.cache_filepath))
        else:
            self.data = {}

    def dump(self):
        json.dump(self.data, open(self.cache_filepath, "w"), indent=2)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data


cache = Cache()


def cached(*cached_args, **cached_kwargs):
    """Cache the return value of the decorated function in memory.

    If a `ttl` keyword argment (of type typedelta) is passed to the decorator,
    the cached value will only be valid for the provided duration.

    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if the decorated function takes a `self` parameter, which is then omitted
            # from the cache key, as we just care about the other arguments, not the class itself.
            if list(inspect.signature(f).parameters.keys())[0] == "self":
                cache_args = args[1:]
            else:
                cache_args = args
            cache_key = "__".join(map(str, cache_args))
            cache_key += "__".join([f"{k}={v}" for k, v in kwargs.items()])
            section = f.__name__
            if section not in cache:
                cache[section] = {}
            if cache_hit := cache[section].get(cache_key):
                if (
                    cache_hit["valid_until"] is None
                    or cache_hit["valid_until"] > time.time()
                ):
                    return cache_hit["data"]
            data = f(*args, **kwargs)
            cache[section][cache_key] = {
                "data": data,
                "valid_until": (
                    (datetime.now() + cached_kwargs["ttl"]).timestamp()
                    if cached_kwargs.get("ttl")
                    else None
                ),
            }
            return data

        return wrapper

    if cached_args and callable(cached_args[0]):
        return decorator(cached_args[0])
    return decorator
