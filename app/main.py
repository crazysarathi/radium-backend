"""Application factory and entrypoint."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.db.session import engine
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(
        "%s starting (env=%s, docs=%s)",
        settings.APP_NAME,
        settings.APP_ENV,
        "off" if settings.is_production else f"{settings.PUBLIC_BASE_URL}/docs",
    )
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception(
            "Database unreachable at startup. If this is a deployed service "
            "(Render, etc.), this almost always means DATABASE_URL (or "
            "POSTGRES_HOST/PORT/USER/PASSWORD/DB) isn't set in that "
            "platform's environment-variable settings — .env is gitignored "
            "and is never uploaded, so the app fell back to its localhost "
            "default. Set those variables in the dashboard and redeploy."
        )
        raise
    yield
    await engine.dispose()
    logger.info("%s stopped", settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "REST API for the Radium website (radium-client) and "
            "admin console (radium-admin)."
        ),
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    # Middleware (outermost first at request time: CORS -> context -> headers).
    # Rate limiting is enforced via a router-level dependency
    # (app/core/rate_limit.py), not SlowAPIMiddleware — see that module's
    # docstring for why the middleware doesn't work with this FastAPI version.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.state.limiter = limiter
    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Serve uploaded files (local storage backend) at /uploads/…
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

    return app


app = create_app()
