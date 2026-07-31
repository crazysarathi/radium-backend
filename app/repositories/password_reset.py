"""Password reset token repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import update

from app.models.password_reset_token import PasswordResetToken
from app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    model = PasswordResetToken

    async def get_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        token = await self.get_by(token_hash=token_hash)
        if token is None or token.is_used or token.expires_at < datetime.now(UTC):
            return None
        return token

    async def mark_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(UTC)
        await self.session.flush()

    async def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )
