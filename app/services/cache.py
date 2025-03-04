import asyncio
import logging
from typing import Any

import redis.asyncio as redis
from fastapi import Request

logger = logging.getLogger(__name__)


class CacheBackend:
    """Abstract cache backend interface."""

    async def get(self, key: str) -> str | None:
        """Get value from cache."""
        raise NotImplementedError()

    async def set(self, key: str, value: str, timeout: int) -> None:
        """Set value in cache with timeout."""
        raise NotImplementedError()


class RedisCacheBackend(CacheBackend):
    """Redis cache backend implementation."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> str | None:
        value = await self.redis.get(key)
        return value.decode("utf-8") if value else None

    async def set(self, key: str, value: str, timeout: int) -> None:
        await self.redis.setex(key, timeout, value)


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend implementation."""

    def __init__(self):
        self.cache: dict[str, dict[str, Any]] = {}
        self._cleanup_lock = asyncio.Lock()

    async def get(self, key: str) -> str | None:
        # Clean expired items occasionally
        if len(self.cache) > 100:  # Simple heuristic to avoid cleaning too often
            asyncio.create_task(self._cleanup_expired())

        item = self.cache.get(key)
        if not item:
            return None

        # Check if expired
        if item["expires"] < asyncio.get_event_loop().time():
            del self.cache[key]
            return None

        return item["value"]

    async def set(self, key: str, value: str, timeout: int) -> None:
        expires = asyncio.get_event_loop().time() + timeout
        self.cache[key] = {"value": value, "expires": expires}

    async def _cleanup_expired(self) -> None:
        # Use a lock to prevent multiple cleanups at once
        async with self._cleanup_lock:
            now = asyncio.get_event_loop().time()
            expired_keys = [
                key for key, item in self.cache.items() if item["expires"] < now
            ]
            for key in expired_keys:
                del self.cache[key]


class CacheService:
    """Service for caching responses."""

    def __init__(
        self,
        cache_type: str,
        default_timeout: int,
        redis_url: str = "redis://localhost:6379/0",
    ):
        """
        Initialize the cache service.

        Args:
            cache_type: Type of cache - "redis" or "memory"
            default_timeout: Default cache expiry time in seconds
            redis_url: Redis connection URL when using Redis cache
        """
        self.default_timeout = default_timeout

        if cache_type.lower() == "redis":
            logger.info(f"Using Redis cache backend with URL: {redis_url}")
            self.backend = RedisCacheBackend(redis_url)
        else:
            logger.info("Using in-memory cache backend")
            self.backend = InMemoryCacheBackend()

    async def get(self, key: str) -> str | None:
        """Get cached value by key."""
        return await self.backend.get(key)

    async def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache with timeout."""
        await self.backend.set(
            key, value, self.default_timeout if timeout is None else timeout
        )


def generate_cache_key(request: Request) -> str:
    """Generate a cache key from request information."""
    query_string = request.url.query or ""
    return f"{request.method}:{request.url.path}:{query_string}"


def custom_cache_timeout(path: str, default_timeout: int) -> int:
    """Get custom cache timeout based on endpoint path."""
    # Static data should be cached longer (15 days)
    if any(path.startswith(prefix) for prefix in ["/ulkeler", "/sehirler", "/ilceler"]):
        return 15 * 24 * 60 * 60  # 15 days

    # All other paths (including /vakitler) use the default timeout (5 days)
    return default_timeout
