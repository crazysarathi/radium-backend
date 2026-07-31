"""Password hashing and JWT creation/verification."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import anyio.to_thread
import bcrypt
import jwt

from app.core.config import settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or of the wrong type."""


# ── Passwords ────────────────────────────────────────────────

# bcrypt only uses the first 72 bytes of input; schemas cap password
# length well below that, this is a defensive backstop.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """Synchronous hash — use `hash_password_async` from request handlers."""
    raw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    raw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(raw, hashed.encode("utf-8"))
    except ValueError:
        return False


# bcrypt burns ~200-400 ms of CPU per call; running it on the event loop would
# stall every other in-flight request, so async callers offload to a thread.
async def hash_password_async(password: str) -> str:
    return await anyio.to_thread.run_sync(hash_password, password)


async def verify_password_async(password: str, hashed: str) -> bool:
    return await anyio.to_thread.run_sync(verify_password, password, hashed)


# Verifying against this when a user is not found keeps login timing
# constant, so attackers cannot enumerate registered emails.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


async def verify_password_dummy() -> None:
    await verify_password_async("invalid-password", _DUMMY_HASH)


# ── JWT ──────────────────────────────────────────────────────


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    """Return (encoded_token, jti, expires_at)."""
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
        "iss": settings.APP_NAME,
        **(extra_claims or {}),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def create_access_token(subject: str, *, role: str) -> tuple[str, datetime]:
    token, _, expires_at = _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        {"role": role},
    )
    return token, expires_at


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Return (token, jti, expires_at) — the jti is persisted for revocation."""
    return _create_token(
        subject,
        TokenType.REFRESH,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.APP_NAME,
            options={"require": ["sub", "type", "jti", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc
    if payload.get("type") != expected_type.value:
        raise TokenError(f"Expected a {expected_type.value} token")
    return payload


# ── Opaque tokens (password reset) ───────────────────────────


def generate_opaque_token() -> tuple[str, str]:
    """Return (token, sha256_hash). Only the hash is stored server-side."""
    token = secrets.token_urlsafe(48)
    return token, hash_opaque_token(token)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
