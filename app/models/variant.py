"""Product variants — one generic table for every family's model line-up.

A variant may carry an optional `code` (a decodable SKU like Jupiter's
six-digit model numbers); families whose variants are named models (chassis,
servers, …) leave it NULL and use `img`/`bullets` for their catalogue cards.
"""

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

VARIANT_STATUSES = ("available", "roadmap")


class Variant(Base, TimestampMixin):
    __tablename__ = "variants"
    __table_args__ = (
        CheckConstraint(f"status IN {VARIANT_STATUSES}", name="status_valid"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str | None] = mapped_column(String(80), unique=True, index=True, nullable=True)
    family: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    rack_units: Mapped[str] = mapped_column(String(10), default="2U")
    img: Mapped[str] = mapped_column(String(300), default="")
    bullets: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="available")
