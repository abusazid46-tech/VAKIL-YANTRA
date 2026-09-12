import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.seed import seed_development_data
from app.db.session import init_database

logger = logging.getLogger("vakil-yantra-api")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend API foundation for Vakil Yantra",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "status": "online",
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    def startup() -> None:
        try:
            init_database()
            seed_development_data()
        except Exception as exc:
            logger.warning(f"Database initialization warning: {exc}")

    return app


app = create_app()
