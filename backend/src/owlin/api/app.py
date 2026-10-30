from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from owlin.api.middleware import BodyLimitMiddleware
from owlin.api.routers import admin, health, me, orders, promo, promotions
from owlin.core.config import get_settings
from owlin.core.errors import AppError


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Owlin API",
        # The interactive docs are only for local development.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(BodyLimitMiddleware)

    # Auth uses the Authorization header, not cookies, so credentials stay off.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(orders.router)
    app.include_router(promo.router)
    app.include_router(promotions.router)
    app.include_router(admin.router)

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, error: AppError) -> JSONResponse:
        return JSONResponse({"detail": error.message}, status_code=error.status_code)

    return app


app = create_app()
