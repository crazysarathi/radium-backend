"""Activity log endpoint — read-only feed for the console's History page."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession
from app.schemas.activity_log import ActivityRead
from app.schemas.common import APIResponse
from app.services.activity_log import ActivityLogService

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("", response_model=APIResponse[list[ActivityRead]])
async def list_activity(session: DBSession, user: CurrentUser) -> APIResponse[list[ActivityRead]]:
    entries = await ActivityLogService(session).list_recent()
    return APIResponse(data=[ActivityRead.model_validate(e) for e in entries])
