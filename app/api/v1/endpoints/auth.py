"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import CurrentUser, DBSession, get_client_ip
from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.common import APIResponse
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

ClientIP = Annotated[str | None, Depends(get_client_ip)]


@router.post("/login", response_model=APIResponse[TokenPair])
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    session: DBSession,
    ip: ClientIP,
) -> APIResponse[TokenPair]:
    pair = await AuthService(session).login(
        body.email,
        body.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip,
    )
    return APIResponse(message="Signed in", data=pair)


@router.post("/refresh", response_model=APIResponse[TokenPair])
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest,
    session: DBSession,
    ip: ClientIP,
) -> APIResponse[TokenPair]:
    pair = await AuthService(session).refresh(
        body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip,
    )
    return APIResponse(message="Token refreshed", data=pair)


@router.post("/logout", response_model=APIResponse[None])
async def logout(body: LogoutRequest, session: DBSession) -> APIResponse[None]:
    await AuthService(session).logout(body.refresh_token)
    return APIResponse(message="Signed out")


@router.post("/logout-all", response_model=APIResponse[dict])
async def logout_all(session: DBSession, user: CurrentUser) -> APIResponse[dict]:
    count = await AuthService(session).logout_all(user)
    return APIResponse(message="Signed out everywhere", data={"sessions_revoked": count})


@router.get("/me", response_model=APIResponse[UserRead])
async def me(user: CurrentUser) -> APIResponse[UserRead]:
    return APIResponse(data=UserRead.model_validate(user))


@router.post("/change-password", response_model=APIResponse[None])
async def change_password(
    body: ChangePasswordRequest, session: DBSession, user: CurrentUser
) -> APIResponse[None]:
    await AuthService(session).change_password(user, body.current_password, body.new_password)
    return APIResponse(message="Password changed. Please sign in again.")


@router.post("/forgot-password", response_model=APIResponse[None])
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def forgot_password(
    request: Request, response: Response, body: ForgotPasswordRequest, session: DBSession
) -> APIResponse[None]:
    await AuthService(session).forgot_password(body.email)
    return APIResponse(
        message="If that email is registered, a reset link has been sent."
    )


@router.post("/reset-password", response_model=APIResponse[None])
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def reset_password(
    request: Request, response: Response, body: ResetPasswordRequest, session: DBSession
) -> APIResponse[None]:
    await AuthService(session).reset_password(body.token, body.new_password)
    return APIResponse(message="Password reset. Please sign in.")
