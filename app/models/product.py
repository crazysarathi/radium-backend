"""Product family model — the catalogue root that variants and accessories hang off."""

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

PRODUCT_STATUSES = ("available", "roadmap")


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(f"status IN {PRODUCT_STATUSES}", name="status_valid"),
    )

    # Immutable id, minted once from the initial slug (matches the admin's
    # historical id === finalSlug behaviour). `slug` is the mutable,
    # publicly-linked identifier other resources (accessories, enquiries)
    # reference — it starts equal to `id` but can drift after a rename.
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    name: Mapped[str] = mapped_column(String(160))
    series: Mapped[str] = mapped_column(String(80))
    tagline: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(ForeignKey("categories.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="available")
    note: Mapped[str] = mapped_column(String(200), default="")
    form_factor: Mapped[str] = mapped_column(String(80), default="")
    has_models: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[str] = mapped_column(Text, default="")

    # Free-shape editor content — arrays of {title, body} / strings /
    # {group, rows} / {label, src}. Kept as JSON rather than normalized
    # tables since the admin UI treats them as opaque ordered blobs.
    highlights: Mapped[list] = mapped_column(JSON, default=list)
    applications: Mapped[list] = mapped_column(JSON, default=list)
    specs: Mapped[list] = mapped_column(JSON, default=list)
    images: Mapped[list] = mapped_column(JSON, default=list)
