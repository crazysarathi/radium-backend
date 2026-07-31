"""Activity log service — records create/update/delete events for the History page."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.repositories.activity_log import ActivityLogRepository

# Mirrors the old client-side log's cap — the History page only ever shows
# the most recent events.
HISTORY_LIMIT = 40


class ActivityLogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ActivityLogRepository(session)

    async def record(self, *, type: str, module: str, label: str) -> None:
        """Flush a new entry — does NOT commit; the caller's transaction does."""
        await self.repo.record(type=type, module=module, label=label)

    async def list_recent(self) -> list[ActivityLog]:
        return await self.repo.list_all(limit=HISTORY_LIMIT)
