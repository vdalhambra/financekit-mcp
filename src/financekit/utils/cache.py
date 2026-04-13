"""Simple TTL-based in-memory cache to minimize API calls."""

import time
from typing import Any


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL."""

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.time() + (ttl if ttl is not None else self._default_ttl)
        self._store[key] = (value, expires_at)

    def clear(self) -> None:
        self._store.clear()

    def cleanup(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]


# Global cache instances with different TTLs
quote_cache = TTLCache(default_ttl=60)        # 1 min for live quotes
history_cache = TTLCache(default_ttl=3600)    # 1 hour for historical data
crypto_cache = TTLCache(default_ttl=120)      # 2 min for crypto prices
info_cache = TTLCache(default_ttl=86400)      # 24h for company info
