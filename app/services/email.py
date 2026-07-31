"""Email service abstraction.

`console` backend logs messages instead of sending them — swap in an SMTP or
provider-based backend later without touching callers.
"""

import logging
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailBackend(ABC):
    @abstractmethod
    async def send(self, *, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailBackend(EmailBackend):
    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info(
            "Email (console backend) from=%s to=%s subject=%r\n%s",
            settings.EMAIL_FROM,
            to,
            subject,
            body,
        )


def get_email_backend() -> EmailBackend:
    if settings.EMAIL_BACKEND == "console":
        return ConsoleEmailBackend()
    raise ValueError(f"Unsupported EMAIL_BACKEND: {settings.EMAIL_BACKEND!r}")


class EmailService:
    def __init__(self, backend: EmailBackend | None = None):
        self.backend = backend or get_email_backend()

    async def send_password_reset(self, *, to: str, token: str) -> None:
        reset_link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?token={token}"
        await self.backend.send(
            to=to,
            subject=f"{settings.APP_NAME} — password reset",
            body=(
                "A password reset was requested for your account.\n\n"
                f"Reset link (valid for {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} "
                f"minutes): {reset_link}\n\n"
                "If you did not request this, you can ignore this email."
            ),
        )
