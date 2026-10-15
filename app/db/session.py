"""Async SQLAlchemy engine and session factory."""

import ssl
from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def build_connect_args(url: str) -> dict:
    """asyncpg connect args for *url* — shared by the app engine and Alembic."""
    parsed = make_url(url)
    host = parsed.host or "localhost"
    args: dict = {}
    # Managed Postgres (Render, Supabase, ...) speaks TLS, but presents a self-signed
    # certificate on a private hostname — strict CA + hostname verification
    # (ssl.create_default_context()) therefore always fails with
    # CERTIFICATE_VERIFY_FAILED. Encrypt the connection without verifying the
    # certificate (equivalent to libpq's sslmode=require, which is what Render
    # documents). A local Postgres gets no SSL at all.
    if host not in ("localhost", "127.0.0.1", "::1"):
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        args["ssl"] = ssl_ctx
    # Supabase's transaction pooler (Supavisor, port 6543) hands each
    # transaction a different server connection, so asyncpg's prepared
    # statements vanish between calls ("prepared statement ... does not
    # exist"). Disable statement caching there; the session pooler (5432)
    # and direct connections keep it.
    if parsed.port == 6543:
        args["statement_cache_size"] = 0
        args["prepared_statement_cache_size"] = 0
    return args


engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args=build_connect_args(settings.async_database_url),
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
