"""
Thread-safe in-memory LRU cache with per-entry TTL.
Used for elevation lookups, geodesic calculations and STAC catalogue metadata.
"""

import time
import threading
from typing import Any, Optional, Dict, Callable
from functools import wraps
from zuhura.core.metrics import record_tile_cache


class ScientificComputationCache:
    """
    High-performance in-memory cache with Least-Recently-Used (LRU) eviction
    and Time-To-Live (TTL) expiration.
    """

    def __init__(self, max_entries: int = 2048, default_ttl_seconds: int = 300):
        self.max_entries = max_entries
        self.default_ttl = default_ttl_seconds
        self._lock = threading.RLock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a cached item if present and not expired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]
            now = time.time()

            # Check expiration
            if entry["expires_at"] < now:
                del self._cache[key]
                self._misses += 1
                return None

            # Update access time (LRU)
            entry["last_accessed"] = now
            self._hits += 1
            return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Stores an item in the cache with a specified or default TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()

        with self._lock:
            # Check capacity and evict least recently used if needed
            if len(self._cache) >= self.max_entries and key not in self._cache:
                self._evict_lru()

            self._cache[key] = {
                "value": value,
                "created_at": now,
                "last_accessed": now,
                "expires_at": now + ttl
            }

    def _evict_lru(self) -> None:
        """Evicts the least recently accessed non-expired entry, or any expired entry."""
        if not self._cache:
            return

        now = time.time()
        # First priority: prune already expired entries
        expired_keys = [k for k, v in self._cache.items() if v["expires_at"] < now]
        if expired_keys:
            for k in expired_keys:
                del self._cache[k]
                self._evictions += 1
            return

        # Second priority: remove least recently accessed entry
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k]["last_accessed"])
        del self._cache[lru_key]
        self._evictions += 1

    def clear(self) -> None:
        """Clears all entries from the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry and operational statistics."""
        with self._lock:
            total_lookups = self._hits + self._misses
            hit_ratio = (self._hits / total_lookups) if total_lookups > 0 else 0.0
            return {
                "total_entries": len(self._cache),
                "max_entries": self.max_entries,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_ratio_pct": round(hit_ratio * 100.0, 2)
            }


# Global singleton instances for different scientific computation domains
global_cache = ScientificComputationCache(max_entries=2048, default_ttl_seconds=600)
orbital_cache = ScientificComputationCache(max_entries=360, default_ttl_seconds=3600)  # Ls indexed


def cached(ttl_seconds: int = 300, key_prefix: str = "", cache_instance: Optional[ScientificComputationCache] = None):
    """
    Decorator for caching deterministic scientific computation results.
    Supports both synchronous and asynchronous functions.
    """
    cache = cache_instance or global_cache

    def decorator(func: Callable):
        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # is coroutine function
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Construct deterministic cache key
                key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cached_val = cache.get(key)
                if cached_val is not None:
                    return cached_val

                result = await func(*args, **kwargs)
                cache.set(key, result, ttl_seconds)
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cached_val = cache.get(key)
                if cached_val is not None:
                    return cached_val

                result = func(*args, **kwargs)
                cache.set(key, result, ttl_seconds)
                return result
            return sync_wrapper

    return decorator
