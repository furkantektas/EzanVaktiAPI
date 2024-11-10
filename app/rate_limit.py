import functools

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request

from .config import get_settings

trusted_clients = get_settings().trusted_clients
rate_limits = ["200 per day", "30 per 5 minutes"]


# Access request object in the limiter.
# Ref: https://github.com/laurentS/slowapi/issues/13#issuecomment-1860629613
def ratelimit(func):
    func = rate_limiter.limiter.limit(rate_limits)(func)

    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        x_parola = request.headers.get("x-parola", "")
        if x_parola in trusted_clients:
            return await func.__wrapped__(request=request, *args, **kwargs)
        return await func(request=request, *args, **kwargs)

    return wrapper


class RateLimit:
    """Wrapper for slowapi.Limiter"""

    def __init__(self, app=None):
        self.app = app
        self.settings = get_settings()
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=rate_limits,
            headers_enabled=True,
            strategy="fixed-window",  # or "moving-window"
            storage_uri=self.settings.redis_url,
        )

        if app is not None:
            self.init_app(app)

    def init_app(self, app) -> None:
        app.state.limiter = self.limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)


rate_limiter = RateLimit()
no_limit = rate_limiter.limiter.exempt
