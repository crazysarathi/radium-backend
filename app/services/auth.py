"""Authentication service: login, token rotation, logout, password lifecycle."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import TokenType
from app.models.user import User
from app.repositories.password_reset import PasswordResetTokenRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenPair
from app.schemas.user import UserRead
from app.services.email import EmailService
from app.utils.network import MAX_IP_LENGTH

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession, email_service: EmailService | None = None):
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.reset_tokens = PasswordResetTokenRepository(session)
        self.email = email_service or EmailService()

    # ── Login / logout ───────────────────────────────────────

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None:
            # Hash anyway so response time doesn't reveal whether the email
            # is registered.
            await security.verify_password_dummy()
            raise UnauthorizedError("Invalid email or password.")
        if not await security.verify_password_async(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")
        return user

    async def login(
        self,
        email: str,
        password: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        user = await self.authenticate(email, password)
        user.last_login_at = datetime.now(UTC)
        pair = await self._issue_token_pair(user, user_agent=user_agent, ip_address=ip_address)
        await self.session.commit()
        return pair

    async def refresh(
        self,
        refresh_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        payload = self._decode_refresh(refresh_token)
        record = await self.refresh_tokens.get_by_jti(payload["jti"])

        if record is None or record.token_hash != security.hash_opaque_token(refresh_token):
            raise UnauthorizedError("Invalid refresh token")

        if record.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token has expired")

        # Read these now: a rollback below would expire the instance, and
        # re-reading its attributes would need lazy IO.
        record_jti, record_user_id = record.jti, record.user_id

        user = await self.users.get(record_user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")

        # Mint the replacement first so its jti can be recorded atomically.
        pair = await self._issue_token_pair(user, user_agent=user_agent, ip_address=ip_address)
        new_jti = security.decode_token(pair.refresh_token, TokenType.REFRESH)["jti"]

        if not await self.refresh_tokens.claim(record_jti, replaced_by_jti=new_jti):
            # The row was already revoked — either a replay of a rotated-away
            # token or a concurrent refresh. Treat as theft: discard the
            # freshly minted token, drop every session, and commit that before
            # the 401 unwinds the request.
            await self.session.rollback()
            revoked = await self.refresh_tokens.revoke_all_for_user(record_user_id)
            await self.session.commit()
            logger.warning(
                "Refresh token reuse detected for user %s — revoked %d sessions",
                record_user_id,
                revoked,
            )
            raise UnauthorizedError("Refresh token has been revoked")

        await self.session.commit()
        return pair

    async def logout(self, refresh_token: str) -> None:
        """Revoke the presented refresh token. Idempotent."""
        try:
            payload = self._decode_refresh(refresh_token)
        except UnauthorizedError:
            return
        record = await self.refresh_tokens.get_by_jti(payload["jti"])
        if record is not None and not record.is_revoked:
            await self.refresh_tokens.revoke(record)
            await self.session.commit()

    async def logout_all(self, user: User) -> int:
        count = await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()
        return count

    # ── Password lifecycle ───────────────────────────────────

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not await security.verify_password_async(current_password, user.hashed_password):
            raise BadRequestError("Current password is incorrect.")
        user.hashed_password = await security.hash_password_async(new_password)
        # Invalidate every existing session.
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()

    async def forgot_password(self, email: str) -> None:
        """Always succeeds — never reveals whether the email is registered."""
        user = await self.users.get_by_email(email)
        # Generate the token either way so both branches do the same work.
        token, token_hash = security.generate_opaque_token()
        if user is None or not user.is_active:
            return
        await self.reset_tokens.invalidate_all_for_user(user.id)
        await self.reset_tokens.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
        await self.session.commit()
        await self.email.send_password_reset(to=user.email, token=token)

    async def reset_password(self, token: str, new_password: str) -> None:
        record = await self.reset_tokens.get_valid_by_hash(security.hash_opaque_token(token))
        if record is None:
            raise BadRequestError("This reset link is invalid or has expired.")
        user = await self.users.get(record.user_id)
        if user is None or not user.is_active:
            raise BadRequestError("This reset link is invalid or has expired.")
        user.hashed_password = await security.hash_password_async(new_password)
        await self.reset_tokens.mark_used(record)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()

    # ── Internals ────────────────────────────────────────────

    async def _issue_token_pair(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenPair:
        access_token, _ = security.create_access_token(str(user.id), role=user.role)
        refresh_token, jti, expires_at = security.create_refresh_token(str(user.id))
        await self.refresh_tokens.create(
            user_id=user.id,
            jti=jti,
            token_hash=security.hash_opaque_token(refresh_token),
            expires_at=expires_at,
            user_agent=(user_agent or "")[:255] or None,
            ip_address=(ip_address or "")[:MAX_IP_LENGTH] or None,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            signed_in_at=datetime.now(UTC).isoformat(),
            user=UserRead.model_validate(user),
        )

    @staticmethod
    def _decode_refresh(refresh_token: str) -> dict:
        try:
            return security.decode_token(refresh_token, TokenType.REFRESH)
        except security.TokenError as exc:
            raise UnauthorizedError(str(exc)) from exc
