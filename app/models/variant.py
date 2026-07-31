"""Product variants — Jupiter's six-digit SKUs and everyone else's chassis models."""

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

VARIANT_STATUSES = ("available", "roadmap")


class JupiterModel(Base, TimestampMixin):
    __tablename__ = "jupiter_models"
    __table_args__ = (
        CheckConstraint(f"status IN {VARIANT_STATUSES}", name="status_valid"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    family: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    rack_units: Mapped[str] = mapped_column(String(10), default="4U")
    status: Mapped[str] = mapped_column(String(20), default="available")


class ChassisModel(Base, TimestampMixin):
    __tablename__ = "chassis_models"
    __table_args__ = (
        CheckConstraint(f"status IN {VARIANT_STATUSES}", name="status_valid"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    model: Mapped[str] = mapped_column(String(80))
    ru: Mapped[str] = mapped_column(String(10), default="2U")
    img: Mapped[str] = mapped_column(String(300), default="")
    bullets: Mapped[list] = mapped_column(JSON, default=list)
    family: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="available")
