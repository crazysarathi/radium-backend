"""User model and roles."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

    @property
    def display_name(self) -> str:
        return _ROLE_DISPLAY[self]


# The radium-admin UI shows the role as a display string (e.g. "Administrator").
_ROLE_DISPLAY = {
    UserRole.ADMIN: "Administrator",
    UserRole.EDITOR: "Editor",
    UserRole.VIEWER: "Viewer",
}


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'editor', 'viewer')", name="role_valid"
        ),
        # Email must be unique among live rows only, so a soft-deleted
        # account doesn't block re-registration of its address.
        Index(
            "uq_users_email_active",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    email: Mapped[str] = mapped_column(String(255), index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.VIEWER.value, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(default=None)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def initials(self) -> str:
        parts = [p for p in self.full_name.split() if p]
        if not parts:
            return self.email[:2].upper()
        return "".join(p[0] for p in parts[:2]).upper()

    @property
    def role_display(self) -> str:
        try:
            return UserRole(self.role).display_name
        except ValueError:
            return self.role.title()
