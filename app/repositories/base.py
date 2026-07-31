"""Generic async repository with pagination, search, sort, and soft delete."""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.db.base import Base, SoftDeleteMixin

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]
    # Columns a client may sort by. Anything else is rejected — client input
    # must never reach getattr() on the model.
    sortable_fields: frozenset[str] = frozenset()
    default_sort_field: str = "created_at"

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Query building ───────────────────────────────────────

    def _base_query(self, include_deleted: bool = False) -> Select:
        query = select(self.model)
        if issubclass(self.model, SoftDeleteMixin) and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        return query

    def _apply_filters(self, query: Select, filters: dict[str, Any] | None) -> Select:
        for field, value in (filters or {}).items():
            if value is None:
                continue
            query = query.where(getattr(self.model, field) == value)
        return query

    def _apply_search(
        self, query: Select, search: str | None, search_fields: list[str]
    ) -> Select:
        if not search or not search_fields:
            return query
        pattern = f"%{search.strip()}%"
        return query.where(
            or_(*(getattr(self.model, field).ilike(pattern) for field in search_fields))
        )

    def _apply_sort(self, query: Select, sort_by: str | None, order: str) -> Select:
        if sort_by is None:
            column = getattr(self.model, self.default_sort_field, self.model.id)
            # Newest first is the default the admin UI expects.
            return query.order_by(column.desc())
        if sort_by not in self.sortable_fields:
            allowed = ", ".join(sorted(self.sortable_fields)) or "none"
            raise BadRequestError(
                f'Cannot sort by "{sort_by}". Sortable fields: {allowed}'
            )
        column = getattr(self.model, sort_by)
        return query.order_by(column.desc() if order == "desc" else column.asc())

    # ── Reads ────────────────────────────────────────────────

    async def get(self, entity_id: Any, *, include_deleted: bool = False) -> ModelT | None:
        query = self._base_query(include_deleted).where(self.model.id == entity_id)
        return await self.session.scalar(query)

    async def get_by(self, *, include_deleted: bool = False, **filters: Any) -> ModelT | None:
        query = self._apply_filters(self._base_query(include_deleted), filters)
        return await self.session.scalar(query.limit(1))

    async def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        order: str = "asc",
        search: str | None = None,
        search_fields: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        """Return (items, total_count) for one page."""
        query = self._base_query()
        query = self._apply_filters(query, filters)
        query = self._apply_search(query, search, search_fields or [])

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        query = self._apply_sort(query, sort_by, order)
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = list((await self.session.scalars(query)).all())
        return items, total

    async def list_all(
        self,
        *,
        order_by: str | None = None,
        order: str = "desc",
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[ModelT]:
        """Return every matching row, unpaginated — for small admin-console collections."""
        query = self._apply_filters(self._base_query(), filters)
        column = getattr(self.model, order_by or self.default_sort_field, self.model.id)
        query = query.order_by(column.desc() if order == "desc" else column.asc())
        if limit is not None:
            query = query.limit(limit)
        return list((await self.session.scalars(query)).all())

    # ── Writes (flush, don't commit — the request scope commits) ──

    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: ModelT, data: dict[str, Any]) -> ModelT:
        for field, value in data.items():
            setattr(instance, field, value)
        await self.session.flush()
        return instance

    async def soft_delete(self, instance: ModelT) -> ModelT:
        if not isinstance(instance, SoftDeleteMixin):
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        instance.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return instance

    async def hard_delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
