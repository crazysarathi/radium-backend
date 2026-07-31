"""Activity log repository."""

from app.models.activity_log import ActivityLog
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository[ActivityLog]):
    model = ActivityLog
    default_sort_field = "at"

    async def record(self, *, type: str, module: str, label: str) -> ActivityLog:
        return await self.create(type=type, module=module, label=label)
