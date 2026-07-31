"""Client address resolution (proxy-aware)."""

from ipaddress import ip_address as parse_ip

from starlette.requests import Request

from app.core.config import settings

# Widest textual IPv6 form (IPv4-mapped) fits in 45 chars — the DB column size.
MAX_IP_LENGTH = 45


def client_ip(request: Request) -> str | None:
    """Resolve the caller's IP, trusting X-Forwarded-For only when configured.

    Without TRUST_PROXY_HEADERS an attacker could spoof the header and get a
    fresh rate-limit bucket per request.
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            candidate = forwarded.split(",")[0].strip()
            if _is_valid_ip(candidate):
                return candidate
    return request.client.host if request.client else None


def _is_valid_ip(value: str) -> bool:
    if not value or len(value) > MAX_IP_LENGTH:
        return False
    try:
        parse_ip(value)
    except ValueError:
        return False
    return True
