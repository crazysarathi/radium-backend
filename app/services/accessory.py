"""Accessory service — catalogue CRUD plus activity logging."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.accessory import Accessory
from app.repositories.accessory import AccessoryRepository
from app.schemas.accessory import AccessoryCreate, AccessoryUpdate
from app.services.activity_log import ActivityLogService

MODULE = "Accessories"


class AccessoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.accessories = AccessoryRepository(session)
        self.activity = ActivityLogService(session)

    async def list_accessories(self) -> list[Accessory]:
        return await self.accessories.list_all(order_by="name", order="asc")

    async def get_accessory(self, accessory_id: str) -> Accessory:
        accessory = await self.accessories.get(accessory_id)
        if accessory is None:
            raise NotFoundError("Accessory not found")
        return accessory

    async def create_accessory(self, data: AccessoryCreate) -> Accessory:
        if await self.accessories.get(data.id) is not None:
            raise ConflictError(f'An accessory with id "{data.id}" already exists.')
        if await self.accessories.sku_exists(data.sku):
            raise ConflictError(f'An accessory with SKU "{data.sku}" already exists.')

        try:
            accessory = await self.accessories.create(**data.model_dump())
            await self.activity.record(
                type="create", module=MODULE, label=f"Added {accessory.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That accessory could not be saved — check the SKU.") from exc
        return accessory

    async def update_accessory(self, accessory_id: str, data: AccessoryUpdate) -> Accessory:
        accessory = await self.get_accessory(accessory_id)
        changes = data.model_dump(exclude_unset=True)
        if "sku" in changes and changes["sku"] != accessory.sku:
            if await self.accessories.sku_exists(changes["sku"]):
                raise ConflictError(f'An accessory with SKU "{changes["sku"]}" already exists.')

        try:
            accessory = await self.accessories.update(accessory, changes)
            await self.activity.record(
                type="update", module=MODULE, label=f"Updated {accessory.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That accessory could not be saved — check the SKU.") from exc
        return accessory

    async def delete_accessory(self, accessory_id: str) -> None:
        accessory = await self.get_accessory(accessory_id)
        name = accessory.name
        await self.accessories.hard_delete(accessory)
        await self.activity.record(type="delete", module=MODULE, label=f"Deleted {name}")
        await self.session.commit()
