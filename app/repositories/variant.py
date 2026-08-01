"""Variant repository — the generic per-family model line-up."""

from app.models.variant import Variant
from app.repositories.base import BaseRepository


class VariantRepository(BaseRepository[Variant]):
    model = Variant
    default_sort_field = "name"

    async def code_exists(self, code: str) -> bool:
        return await self.get_by(code=code) is not None
