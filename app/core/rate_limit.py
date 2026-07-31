"""Shared slowapi limiter instance (memory-backed now, Redis-ready via config).

The default limit is enforced via `enforce_default_rate_limit` below, NOT via
`SlowAPIMiddleware`. On the installed FastAPI/slowapi versions, routes added
through `include_router()` are wrapped in an internal `_IncludedRouter` object
that lacks the `.endpoint` attribute slowapi's middleware looks for, so its
route-matching silently finds nothing and the "default" limit never fires for
any real endpoint — confirmed by tracing `slowapi.middleware._find_route_handler`
against this app's routes. A dependency runs after FastAPI has already
resolved the route, sidestepping that broken lookup entirely.
"""

from fastapi import Request
from slowapi import Limiter

from app.core.config import settings
from app.utils.network import client_ip


def _rate_limit_key(request: Request) -> str:
    return client_ip(request) or "unknown"


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    headers_enabled=True,
)


async def enforce_default_rate_limit(request: Request) -> None:
    """Apply RATE_LIMIT_DEFAULT to any route without its own `@limiter.limit(...)`.

    Routes that already carry an explicit decorator (login/refresh/…) are
    skipped here — they enforce their own, stricter limit when called, and
    checking both would double-count each request against the same window.
    """
    route = request.scope.get("route")
    endpoint = getattr(route, "endpoint", None)
    if endpoint is None:
        return
    endpoint_name = f"{endpoint.__module__}.{endpoint.__name__}"
    if endpoint_name in limiter._route_limits:
        return
    limiter._check_request_limit(request, endpoint, in_middleware=False)
