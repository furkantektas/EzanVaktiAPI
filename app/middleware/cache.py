import hashlib
import json
import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import Response as StarletteResponse

from app.infrastructure.cache.service import (
    CacheService,
    custom_cache_timeout,
    generate_cache_key,
)

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        cache_service: CacheService,
        excluded_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.cache_service = cache_service
        self.excluded_paths = excluded_paths or ["/up"]

    def generate_etag(self, content: str) -> str:
        """Generate an ETag for the given content."""
        return hashlib.md5(content.encode()).hexdigest()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip caching for excluded paths or non-GET requests
        if request.method != "GET" or any(
            request.url.path.startswith(path) for path in self.excluded_paths
        ):
            return await call_next(request)

        # Generate cache key from request
        cache_key = generate_cache_key(request)

        # Try to get from cache
        cached_response = await self.cache_service.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for {request.url.path}")
            cached_data = json.loads(cached_response)

            # Recreate the response from cached data
            content = cached_data["content"]
            status_code = cached_data["status_code"]
            headers = cached_data["headers"]

            # Generate ETag
            etag = cached_data.get("etag") or self.generate_etag(json.dumps(content))

            # Check if client sent If-None-Match header
            if_none_match = request.headers.get("If-None-Match")
            if if_none_match and if_none_match == etag:
                # Return 304 Not Modified if ETags match
                response = StarletteResponse(status_code=304)
                response.headers["ETag"] = etag
                return response

            # Create normal response with content
            response = JSONResponse(content=content, status_code=status_code)

            # Apply headers from cached response
            for key, value in headers.items():
                if key.lower() not in ("content-length", "content-encoding"):
                    response.headers[key] = value

            # Set ETag header
            response.headers["ETag"] = etag
            # Set cache header to indicate a cache hit
            response.headers["X-Cache"] = "HIT"
            return response

        # Process the request if not in cache
        response = await call_next(request)

        # Only cache successful JSON responses
        if (
            hasattr(response, "status_code")
            and response.status_code == 200
            and response.headers.get("content-type", "").startswith("application/json")
        ):
            # Need to extract the response content for caching
            response_body = b""

            async for chunk in response.body_iterator:
                response_body += chunk

            # Reconstruct response for the client
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            try:
                # Parse the JSON content
                json_content = json.loads(response_body)

                # Generate ETag for the response
                etag = self.generate_etag(json.dumps(json_content))
                response.headers["ETag"] = etag

                # Get appropriate timeout for this path
                path_timeout = custom_cache_timeout(
                    request.url.path, self.cache_service.default_timeout
                )

                # Store response in cache with the custom timeout
                cache_data = {
                    "content": json_content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "etag": etag,
                }
                await self.cache_service.set(
                    cache_key, json.dumps(cache_data), timeout=path_timeout
                )

                # Add header to indicate this was a cache miss
                response.headers["X-Cache"] = "MISS"

            except Exception as e:
                logger.error(f"Error caching response: {str(e)}")

        return response
