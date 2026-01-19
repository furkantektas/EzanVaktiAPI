from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from requests.exceptions import RequestException

from app.core.config import get_settings
from app.core.errors import diyanet_exception_handler
from app.infrastructure.cache.service import CacheService, custom_cache_timeout
from app.middleware.cache import CacheMiddleware
from app.routes import router

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    summary="Diyanet İşleri Başkanlığı tarafından yayınlanan ezan vakitlerini sağlar.",
    version=settings.api_version,
)

# Initialize cache service
cache_service = CacheService(
    cache_type=settings.cache_type,
    default_timeout=settings.cache_default_timeout,
    redis_url=settings.redis_url,
)

# Add middleware in order (order matters for middleware)
# Cache middleware should be before GZip to cache uncompressed responses
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CacheMiddleware,  # type: ignore
    cache_service=cache_service,
    excluded_paths=settings.cache_excluded_paths,
)
app.add_middleware(GZipMiddleware, minimum_size=500)  # type: ignore[arg-type]


@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)

    # Add Cache-Control header for GET requests to relevant endpoints
    if request.method == "GET" and not any(
        request.url.path.startswith(path) for path in settings.cache_excluded_paths
    ):
        # Calculate appropriate timeout for this path
        path_timeout = custom_cache_timeout(
            request.url.path, settings.cache_default_timeout
        )
        response.headers["Cache-Control"] = f"public, max-age={path_timeout}"

    return response


@app.middleware("http")
async def set_utf8_charset(request: Request, call_next):
    response = await call_next(request)

    # Ensure JSON responses include UTF-8 charset for non-ASCII characters
    if response.headers.get("content-type") == "application/json":
        response.headers["content-type"] = "application/json; charset=utf-8"

    return response


app.include_router(router)

# Register exception handlers
app.add_exception_handler(RequestException, diyanet_exception_handler)  # type: ignore
