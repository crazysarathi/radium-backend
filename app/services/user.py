"""User management service (admin-facing)."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password_async
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import USER_SEARCH_FIELDS, UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.utils.pagination import ListParams


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)

    async def list_users(
        self, params: ListParams, *, role: str | None = None, is_active: bool | None = None
    ) -> tuple[list[User], int]:
        return await self.users.list_paginated(
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            order=params.order,
            search=params.search,
            search_fields=USER_SEARCH_FIELDS,
            filters={"role": role, "is_active": is_active},
        )

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def create_user(self, data: UserCreate) -> User:
        email = data.email.strip().lower()
        if await self.users.email_exists(email):
            raise ConflictError(f'A user with email "{email}" already exists.')
        try:
            user = await self.users.create(
                email=email,
                hashed_password=await hash_password_async(data.password),
                full_name=data.full_name.strip(),
                role=data.role.value,
                is_active=data.is_active,
            )
            await self.session.commit()
        except IntegrityError as exc:
            # Lost the race against a concurrent create with the same email;
            # the partial unique index is the real guard.
            await self.session.rollback()
            raise ConflictError(f'A user with email "{email}" already exists.') from exc
        return user

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate, *, acting_user: User) -> User:
        user = await self.get_user(user_id)
        changes = data.model_dump(exclude_unset=True)
        if user.id == acting_user.id and changes.get("is_active") is False:
            raise BadRequestError("You cannot deactivate your own account.")
        if "role" in changes:
            changes["role"] = changes["role"].value
            if user.id == acting_user.id:
                raise BadRequestError("You cannot change your own role.")
        if "full_name" in changes:
            changes["full_name"] = changes["full_name"].strip()
        user = await self.users.update(user, changes)
        if changes.get("is_active") is False:
            await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()
        return user

    async def delete_user(self, user_id: uuid.UUID, *, acting_user: User) -> None:
        if user_id == acting_user.id:
            raise BadRequestError("You cannot delete your own account.")
        user = await self.get_user(user_id)
        await self.users.soft_delete(user)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()
