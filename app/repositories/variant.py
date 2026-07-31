"""Variant repositories — Jupiter models and chassis models."""

from app.models.variant import ChassisModel, JupiterModel
from app.repositories.base import BaseRepository


class JupiterModelRepository(BaseRepository[JupiterModel]):
    model = JupiterModel
    default_sort_field = "code"

    async def code_exists(self, code: str) -> bool:
        return await self.get_by(code=code) is not None


class ChassisModelRepository(BaseRepository[ChassisModel]):
    model = ChassisModel
    default_sort_field = "model"
