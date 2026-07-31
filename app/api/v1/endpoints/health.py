"""Liveness and readiness probes."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DBSession
from app.core.config import settings
from app.schemas.common import APIResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=APIResponse[dict])
async def liveness() -> APIResponse[dict]:
    return APIResponse(data={"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV})


@router.get("/health/ready", response_model=APIResponse[dict])
async def readiness(session: DBSession) -> APIResponse[dict]:
    await session.execute(text("SELECT 1"))
    return APIResponse(data={"status": "ready", "database": "up"})
