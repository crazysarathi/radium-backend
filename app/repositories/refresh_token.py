"""Refresh token repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import update

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken
    sortable_fields = frozenset({"created_at", "expires_at", "revoked_at"})

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        return await self.get_by(jti=jti)

    async def claim(self, jti: str, *, replaced_by_jti: str) -> bool:
        """Atomically revoke an active token; True if this caller won the race.

        Two concurrent refreshes with the same token would otherwise both
        succeed — the conditional UPDATE lets exactly one through, and the
        loser is treated as token reuse.
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.jti == jti, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC), replaced_by_jti=replaced_by_jti)
        )
        return (result.rowcount or 0) == 1

    async def revoke(self, token: RefreshToken, *, replaced_by_jti: str | None = None) -> None:
        token.revoked_at = datetime.now(UTC)
        token.replaced_by_jti = replaced_by_jti
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        return result.rowcount or 0
