import logging

from fastapi import Request

from app.infrastructure.cache.backends import InMemoryCacheBackend, RedisCacheBackend

logger = logging.getLogger(__name__)


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
