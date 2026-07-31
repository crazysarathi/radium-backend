"""User repository."""

from app.models.user import User
from app.repositories.base import BaseRepository

USER_SEARCH_FIELDS = ["email", "full_name"]


class UserRepository(BaseRepository[User]):
    model = User
    sortable_fields = frozenset(
        {"email", "full_name", "role", "is_active", "created_at", "updated_at", "last_login_at"}
    )

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by(email=email.strip().lower())

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None
