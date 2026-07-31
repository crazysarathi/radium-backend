"""Accessories — rails, trays, drives, etc, tagged with the product ids they fit."""

from sqlalchemy import JSON, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

ACCESSORY_STATUSES = ("available", "roadmap")


class Accessory(Base, TimestampMixin):
    __tablename__ = "accessories"
    __table_args__ = (
        CheckConstraint(f"status IN {ACCESSORY_STATUSES}", name="status_valid"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    # Product ids this accessory is tagged for — a plain JSON list rather
    # than an association table, since it's only ever read/written whole.
    # Column is named for_products (not "for" — a reserved SQL keyword);
    # the ORM/schema attribute is `for_`, matching the frontend's `for` key.
    for_: Mapped[list] = mapped_column("for_products", JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="available")
