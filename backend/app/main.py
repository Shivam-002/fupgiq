from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.handlers import UnhandledErrorMiddleware, register_exception_handlers
from app.core.logging_config import setup_logging
from app.dependencies import get_wind_provider
from app.routers import forecast, health


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await get_wind_provider().aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.name,
        version=settings.version,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )

    # outermost, so 500s get CORS headers
    app.add_middleware(UnhandledErrorMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(forecast.router, prefix="/api")
    return app


app = create_app()
