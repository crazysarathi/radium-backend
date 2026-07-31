"""Product category lookup table."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    blurb: Mapped[str | None] = mapped_column(Text, default=None)

    @property
    def key(self) -> str:
        """Alias of `id` — the admin UI historically calls this field `key`."""
        return self.id
