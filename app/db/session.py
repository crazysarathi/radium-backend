"""Async SQLAlchemy engine and session factory."""

import ssl
from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Managed Postgres (Render, etc.) speaks TLS, but presents a self-signed
# certificate on a private hostname — strict CA + hostname verification
# (ssl.create_default_context()) therefore always fails with
# CERTIFICATE_VERIFY_FAILED. Encrypt the connection without verifying the
# certificate (equivalent to libpq's sslmode=require, which is what Render
# documents). A local Postgres gets no SSL at all.
_db_host = make_url(settings.async_database_url).host or "localhost"
_connect_args: dict = {}
if _db_host not in ("localhost", "127.0.0.1", "::1"):
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
    _connect_args["ssl"] = _ssl_ctx

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Request-scoped session.

    Services own the transaction boundary and commit explicitly, so a commit
    failure is raised inside the handler and becomes a proper error response.
    Committing here (in dependency teardown) would run after the response was
    already built and could report success for a transaction that never landed.
    Anything still uncommitted when the request ends is rolled back.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
