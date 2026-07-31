"""User schemas."""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import ORMModel

# bcrypt ignores input beyond 72 bytes, so cap passwords well below that.
PasswordField = Field(min_length=8, max_length=64)


class UserRead(ORMModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    role_display: str
    initials: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserCreate(ORMModel):
    email: EmailStr
    password: str = PasswordField
    full_name: str = Field(min_length=1, max_length=120)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserUpdate(ORMModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None
