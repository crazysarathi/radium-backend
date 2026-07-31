"""Product service — catalogue CRUD plus activity logging."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.activity_log import ActivityLogService

MODULE = "Products"


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.products = ProductRepository(session)
        self.categories = CategoryRepository(session)
        self.activity = ActivityLogService(session)

    async def list_products(self) -> list[Product]:
        return await self.products.list_all(order_by="name", order="asc")

    async def get_product(self, product_id: str) -> Product:
        product = await self.products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def _check_category(self, category_id: str) -> None:
        if await self.categories.get(category_id) is None:
            raise BadRequestError(f'Unknown category "{category_id}".')

    async def create_product(self, data: ProductCreate) -> Product:
        if await self.products.get(data.id) is not None:
            raise ConflictError(f'A product with id "{data.id}" already exists.')
        slug = data.slug or data.id
        if await self.products.slug_exists(slug):
            raise ConflictError(f'A product with slug "{slug}" already exists.')
        await self._check_category(data.category)

        payload = data.model_dump(exclude={"slug"})
        try:
            product = await self.products.create(slug=slug, **payload)
            await self.activity.record(
                type="create", module=MODULE, label=f"Added {product.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That product could not be saved — check the id and slug.") from exc
        return product

    async def update_product(self, product_id: str, data: ProductUpdate) -> Product:
        product = await self.get_product(product_id)
        changes = data.model_dump(exclude_unset=True)

        if "slug" in changes and changes["slug"] not in (None, product.slug):
            if await self.products.slug_exists(changes["slug"], exclude_id=product_id):
                raise ConflictError(f'A product with slug "{changes["slug"]}" already exists.')
        if "category" in changes and changes["category"]:
            await self._check_category(changes["category"])

        try:
            product = await self.products.update(product, changes)
            await self.activity.record(
                type="update", module=MODULE, label=f"Updated {product.name}"
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That product could not be saved — check the slug.") from exc
        return product

    async def delete_product(self, product_id: str) -> None:
        product = await self.get_product(product_id)
        name = product.name
        await self.products.hard_delete(product)
        await self.activity.record(type="delete", module=MODULE, label=f"Deleted {name}")
        await self.session.commit()
