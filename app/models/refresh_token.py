"""Persisted refresh tokens — enables revocation, rotation, and reuse detection."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    # jti claim of the JWT; the token itself is never stored, only its hash.
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
    # Set on rotation; a revoked-but-reused token indicates theft.
    replaced_by_jti: Mapped[str | None] = mapped_column(String(36), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(255), default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), default=None)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")  # noqa: F821

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None
