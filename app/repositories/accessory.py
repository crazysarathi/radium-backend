"""Accessory repository."""

from app.models.accessory import Accessory
from app.repositories.base import BaseRepository


class AccessoryRepository(BaseRepository[Accessory]):
    model = Accessory
    default_sort_field = "name"

    async def sku_exists(self, sku: str) -> bool:
        return await self.get_by(sku=sku) is not None
