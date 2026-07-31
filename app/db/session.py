"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
import ssl

# engine = create_async_engine(
#     settings.async_database_url,
#     echo=settings.DB_ECHO,
#     pool_pre_ping=True,
#     pool_size=settings.DB_POOL_SIZE,
#     max_overflow=settings.DB_MAX_OVERFLOW,
# )


ssl_context = ssl.create_default_context()

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={"ssl": ssl_context},
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
