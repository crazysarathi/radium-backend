"""Variant service — one generic model line-up shared by every product family.

Auto-flips the parent product's `has_models` flag on the first variant, same
as the admin UI used to do client-side — done here instead so it can't drift
and doesn't spam the activity feed with a synthetic "product updated".
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.variant import Variant
from app.repositories.product import ProductRepository
from app.repositories.variant import VariantRepository
from app.schemas.variant import VariantCreate, VariantUpdate
from app.services.activity_log import ActivityLogService

VARIANT_MODULE = "Variants"


class VariantService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.variants = VariantRepository(session)
        self.products = ProductRepository(session)
        self.activity = ActivityLogService(session)

    async def _check_family(self, family: str) -> None:
        if await self.products.get(family) is None:
            raise BadRequestError(f'Unknown product family "{family}".')

    async def _flag_has_models(self, family: str) -> None:
        product = await self.products.get(family)
        if product is not None and not product.has_models:
            await self.products.update(product, {"has_models": True})

    async def list_variants(self, family: str | None = None) -> list[Variant]:
        return await self.variants.list_all(
            order_by="name", order="asc", filters={"family": family} if family else None
        )

    async def get_variant(self, variant_id: str) -> Variant:
        variant = await self.variants.get(variant_id)
        if variant is None:
            raise NotFoundError("Variant not found")
        return variant

    async def create_variant(self, data: VariantCreate) -> Variant:
        if await self.variants.get(data.id) is not None:
            raise ConflictError(f'A variant with id "{data.id}" already exists.')
        if data.code is not None and await self.variants.code_exists(data.code):
            raise ConflictError(f'Model number "{data.code}" already exists.')
        await self._check_family(data.family)

        try:
            variant = await self.variants.create(**data.model_dump())
            await self._flag_has_models(data.family)
            await self.activity.record(
                type="create", module=VARIANT_MODULE, label=f"Added {variant.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That variant could not be saved.") from exc
        return variant

    async def update_variant(self, variant_id: str, data: VariantUpdate) -> Variant:
        variant = await self.get_variant(variant_id)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("code") is not None and changes["code"] != variant.code:
            if await self.variants.code_exists(changes["code"]):
                raise ConflictError(f'Model number "{changes["code"]}" already exists.')
        if changes.get("family"):
            await self._check_family(changes["family"])

        try:
            variant = await self.variants.update(variant, changes)
            await self.activity.record(
                type="update", module=VARIANT_MODULE, label=f"Updated {variant.name}"
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
        await self.activity.record(type="delete", module=VARIANT_MODULE, label=f"Deleted {name}")
        await self.session.commit()
