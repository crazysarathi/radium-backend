"""User management endpoints (admin only)."""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, DBSession
from app.models.user import UserRole
from app.schemas.common import APIResponse, PageMeta, PaginatedResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import UserService
from app.utils.pagination import ListParamsDep

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserRead])
async def list_users(
    session: DBSession,
    admin: AdminUser,
    params: ListParamsDep,
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> PaginatedResponse[UserRead]:
    users, total = await UserService(session).list_users(
        params, role=role.value if role else None, is_active=is_active
    )
    return PaginatedResponse(
        data=[UserRead.model_validate(u) for u in users],
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total_items=total),
    )


@router.post("", response_model=APIResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate, session: DBSession, admin: AdminUser
) -> APIResponse[UserRead]:
    user = await UserService(session).create_user(body)
    return APIResponse(message="User created", data=UserRead.model_validate(user))


@router.get("/{user_id}", response_model=APIResponse[UserRead])
async def get_user(
    user_id: uuid.UUID, session: DBSession, admin: AdminUser
) -> APIResponse[UserRead]:
    user = await UserService(session).get_user(user_id)
    return APIResponse(data=UserRead.model_validate(user))


@router.patch("/{user_id}", response_model=APIResponse[UserRead])
async def update_user(
    user_id: uuid.UUID, body: UserUpdate, session: DBSession, admin: AdminUser
) -> APIResponse[UserRead]:
    user = await UserService(session).update_user(user_id, body, acting_user=admin)
    return APIResponse(message="User updated", data=UserRead.model_validate(user))


@router.delete("/{user_id}", response_model=APIResponse[None])
async def delete_user(
    user_id: uuid.UUID, session: DBSession, admin: AdminUser
) -> APIResponse[None]:
    await UserService(session).delete_user(user_id, acting_user=admin)
    return APIResponse(message="User deleted")
