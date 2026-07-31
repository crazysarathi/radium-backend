"""Variant services — Jupiter's six-digit SKUs and everyone else's chassis models.

Both auto-flip the parent product's `has_models` flag on the first variant,
same as the admin UI used to do client-side — done here instead so it can't
drift and doesn't spam the activity feed with a synthetic "product updated".
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.variant import ChassisModel, JupiterModel
from app.repositories.product import ProductRepository
from app.repositories.variant import ChassisModelRepository, JupiterModelRepository
from app.schemas.variant import (
    ChassisModelCreate,
    ChassisModelUpdate,
    JupiterModelCreate,
    JupiterModelUpdate,
)
from app.services.activity_log import ActivityLogService

JUPITER_MODULE = "Jupiter Models"
CHASSIS_MODULE = "Chassis Models"


class _VariantServiceBase:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.products = ProductRepository(session)
        self.activity = ActivityLogService(session)

    async def _check_family(self, family: str) -> None:
        if await self.products.get(family) is None:
            raise BadRequestError(f'Unknown product family "{family}".')

    async def _flag_has_models(self, family: str) -> None:
        product = await self.products.get(family)
        if product is not None and not product.has_models:
            await self.products.update(product, {"has_models": True})


class JupiterModelService(_VariantServiceBase):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.variants = JupiterModelRepository(session)

    async def list_variants(self) -> list[JupiterModel]:
        return await self.variants.list_all(order_by="code", order="asc")

    async def get_variant(self, variant_id: str) -> JupiterModel:
        variant = await self.variants.get(variant_id)
        if variant is None:
            raise NotFoundError("Variant not found")
        return variant

    async def create_variant(self, data: JupiterModelCreate) -> JupiterModel:
        if await self.variants.get(data.id) is not None:
            raise ConflictError(f'A variant with id "{data.id}" already exists.')
        if await self.variants.code_exists(data.code):
            raise ConflictError(f'Model number "{data.code}" already exists.')
        await self._check_family(data.family)

        try:
            variant = await self.variants.create(**data.model_dump())
            await self._flag_has_models(data.family)
            await self.activity.record(
                type="create", module=JUPITER_MODULE, label=f"Added {variant.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That variant could not be saved.") from exc
        return variant

    async def update_variant(self, variant_id: str, data: JupiterModelUpdate) -> JupiterModel:
        variant = await self.get_variant(variant_id)
        changes = data.model_dump(exclude_unset=True)
        if "code" in changes and changes["code"] != variant.code:
            if await self.variants.code_exists(changes["code"]):
                raise ConflictError(f'Model number "{changes["code"]}" already exists.')
        if "family" in changes and changes["family"]:
            await self._check_family(changes["family"])

        try:
            variant = await self.variants.update(variant, changes)
            await self.activity.record(
                type="update", module=JUPITER_MODULE, label=f"Updated {variant.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That variant could not be saved.") from exc
        return variant

    async def delete_variant(self, variant_id: str) -> None:
        variant = await self.get_variant(variant_id)
        name = variant.name
        await self.variants.hard_delete(variant)
        await self.activity.record(type="delete", module=JUPITER_MODULE, label=f"Deleted {name}")
        await self.session.commit()


class ChassisModelService(_VariantServiceBase):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.variants = ChassisModelRepository(session)

    async def list_variants(self) -> list[ChassisModel]:
        return await self.variants.list_all(order_by="model", order="asc")

    async def get_variant(self, variant_id: str) -> ChassisModel:
        variant = await self.variants.get(variant_id)
        if variant is None:
            raise NotFoundError("Variant not found")
        return variant

    async def create_variant(self, data: ChassisModelCreate) -> ChassisModel:
        if await self.variants.get(data.id) is not None:
            raise ConflictError(f'A variant with id "{data.id}" already exists.')
        await self._check_family(data.family)

        try:
            variant = await self.variants.create(**data.model_dump())
            await self._flag_has_models(data.family)
            await self.activity.record(
                type="create", module=CHASSIS_MODULE, label=f"Added {variant.model}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That variant could not be saved.") from exc
        return variant

    async def update_variant(self, variant_id: str, data: ChassisModelUpdate) -> ChassisModel:
        variant = await self.get_variant(variant_id)
        changes = data.model_dump(exclude_unset=True)
        if "family" in changes and changes["family"]:
            await self._check_family(changes["family"])

        try:
            variant = await self.variants.update(variant, changes)
            await self.activity.record(
                type="update", module=CHASSIS_MODULE, label=f"Updated {variant.model}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That variant could not be saved.") from exc
        return variant

    async def delete_variant(self, variant_id: str) -> None:
        variant = await self.get_variant(variant_id)
        name = variant.model
        await self.variants.hard_delete(variant)
        await self.activity.record(type="delete", module=CHASSIS_MODULE, label=f"Deleted {name}")
        await self.session.commit()
