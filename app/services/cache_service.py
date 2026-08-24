import time
import hashlib
import json
from typing import Any, Dict, Callable
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a cached entry with expiration."""
    value: Any
    expires_at: float


class CacheService:
    """In-memory caching service for hot-path query optimization."""

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        """Initializes cache with default TTL."""
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Retrieves value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        if time.time() > entry.expires_at:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Stores value in cache with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> None:
        """Removes key from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clears all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        # Clean expired entries
        now = time.time()
        expired_keys = [k for k, v in self._cache.items() if now > v.expires_at]
        for k in expired_keys:
            del self._cache[k]

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
        }

    def make_key(self, *args, **kwargs) -> str:
        """Creates a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def cached(self, ttl_seconds: int | None = None):
        """Decorator for caching function results."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{self.make_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds)
                return result
            
            return wrapper
        return decorator


# Specialized caching methods for common use cases
class QueryCacheService(CacheService):
    """Extended cache service with domain-specific methods."""

    def cache_customer_360(self, customer_id: str, data: Dict, ttl: int = 180) -> None:
        """Caches Customer 360 profile data."""
        self.set(f"customer_360:{customer_id}", data, ttl)

    def get_customer_360(self, customer_id: str) -> Dict | None:
        """Retrieves cached Customer 360 profile."""
        return self.get(f"customer_360:{customer_id}")

    def cache_opportunity_scan(self, merchant_id: str, data: Dict, ttl: int = 300) -> None:
        """Caches opportunity scan results."""
        self.set(f"opportunity_scan:{merchant_id}", data, ttl)

    def get_opportunity_scan(self, merchant_id: str) -> Dict | None:
        """Retrieves cached opportunity scan."""
        return self.get(f"opportunity_scan:{merchant_id}")

    def cache_rfm_segments(self, merchant_id: str, data: Dict, ttl: int = 600) -> None:
        """Caches RFM segmentation results."""
        self.set(f"rfm_segments:{merchant_id}", data, ttl)

    def get_rfm_segments(self, merchant_id: str) -> Dict | None:
        """Retrieves cached RFM segments."""
        return self.get(f"rfm_segments:{merchant_id}")

    def invalidate_merchant(self, merchant_id: str) -> None:
        """Invalidates all cache entries for a merchant."""
        patterns = [
            f"customer_360:*{merchant_id}*",
            f"opportunity_scan:{merchant_id}",
            f"rfm_segments:{merchant_id}",
        ]
        # Simple prefix matching for invalidation
        for key in list(self._cache.keys()):
            for pattern in patterns:
                if merchant_id in key:
                    self.delete(key)


# Global singleton instance
query_cache_service = QueryCacheService(default_ttl_seconds=300)
