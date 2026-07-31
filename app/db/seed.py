"""Idempotent database seeding: creates the first superuser.

Run with:  python -m app.db.seed
"""

import asyncio
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.security import hash_password_async
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        existing = await users.get_by_email(settings.FIRST_SUPERUSER_EMAIL)
        if existing is not None:
            logger.info("Superuser %s already exists — nothing to do", existing.email)
            return
        user = User(
            email=settings.FIRST_SUPERUSER_EMAIL.strip().lower(),
            hashed_password=await hash_password_async(settings.FIRST_SUPERUSER_PASSWORD),
            full_name=settings.FIRST_SUPERUSER_NAME,
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        logger.info("Created superuser %s", user.email)


async def main() -> None:
    configure_logging()
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
