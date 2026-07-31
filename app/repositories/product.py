"""Product repository."""

from app.models.product import Product
from app.repositories.base import BaseRepository

PRODUCT_SEARCH_FIELDS = ["name", "series", "tagline"]


class ProductRepository(BaseRepository[Product]):
    model = Product
    sortable_fields = frozenset({"name", "series", "status", "created_at", "updated_at"})

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        existing = await self.get_by(slug=slug)
        return existing is not None and existing.id != exclude_id
