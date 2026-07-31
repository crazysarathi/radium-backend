"""Shared API dependencies: DB session, current user, RBAC."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, TokenType, decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.utils.network import client_ip

get_client_ip = client_ip

DBSession = Annotated[AsyncSession, Depends(get_db)]

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session: DBSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ] = None,
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    try:
        payload = decode_token(credentials.credentials, TokenType.ACCESS)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise UnauthorizedError("Invalid token") from exc

    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("This account has been deactivated.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """Dependency factory: allow only users whose role is in `roles`."""

    allowed = {role.value for role in roles}

    async def checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise ForbiddenError()
        return user

    return Depends(checker)


AdminUser = Annotated[User, require_roles(UserRole.ADMIN)]
# Roles allowed to modify content (products, media, …).
WriterUser = Annotated[User, require_roles(UserRole.ADMIN, UserRole.EDITOR)]
