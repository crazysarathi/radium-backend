"""Activity feed — server-recorded create/update/delete events for the console history page."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin

ACTIVITY_TYPES = ("create", "update", "delete")


class ActivityLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "activity_log"
    __table_args__ = (
        CheckConstraint(f"type IN {ACTIVITY_TYPES}", name="type_valid"),
    )

    type: Mapped[str] = mapped_column(String(10))
    module: Mapped[str] = mapped_column(String(60))
    label: Mapped[str] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
