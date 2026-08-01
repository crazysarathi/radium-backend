"""Category service — catalogue lookup CRUD plus activity logging."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.product import Product
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.activity_log import ActivityLogService

MODULE = "Categories"


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.categories = CategoryRepository(session)
        self.activity = ActivityLogService(session)

    async def list_categories(self) -> list[Category]:
        return await self.categories.list_all(order_by="label", order="asc")

    async def get_category(self, category_id: str) -> Category:
        category = await self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def count_products(self, category_id: str) -> int:
        count = await self.session.scalar(
            select(func.count()).select_from(Product).where(Product.category == category_id)
        )
        return count or 0

    async def create_category(self, data: CategoryCreate) -> Category:
        if await self.categories.get(data.id) is not None:
            raise ConflictError(f'A category with key "{data.id}" already exists.')
        category = await self.categories.create(**data.model_dump())
        await self.activity.record(type="create", module=MODULE, label=f"Added {category.label}")
        await self.session.commit()
        return category

    async def update_category(self, category_id: str, data: CategoryUpdate) -> Category:
        category = await self.get_category(category_id)
        category = await self.categories.update(category, data.model_dump(exclude_unset=True))
        await self.activity.record(type="update", module=MODULE, label=f"Updated {category.label}")
        await self.session.commit()
        return category

    async def delete_category(self, category_id: str) -> None:
        category = await self.get_category(category_id)
        in_use = await self.count_products(category_id)
        if in_use:
            plural = "product" if in_use == 1 else "products"
            raise ConflictError(
                f'"{category.label}" is still assigned to {in_use} {plural} — '
                "move them to another category first."
            )
        label = category.label
        await self.categories.hard_delete(category)
        await self.activity.record(type="delete", module=MODULE, label=f"Deleted {label}")
        await self.session.commit()
