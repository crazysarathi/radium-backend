"""Contact-form enquiries landing in the admin inbox."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

ENQUIRY_STATUSES = ("new", "replied", "closed")


class Enquiry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "enquiries"
    __table_args__ = (
        CheckConstraint(f"status IN {ENQUIRY_STATUSES}", name="status_valid"),
    )

    name: Mapped[str] = mapped_column(String(160))
    org: Mapped[str] = mapped_column(String(160), default="")
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(40), default="")
    # Loosely references a product id/slug — kept as free text so an
    # enquiry survives the referenced product being renamed or deleted.
    interest: Mapped[str] = mapped_column(String(80), default="")
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


__all__ = ["Enquiry", "ENQUIRY_STATUSES"]
