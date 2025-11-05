"""FastAPI application entry point for MindDock backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import api
from app.config import get_settings
from app.database import Base, engine
from app.workflows import initialize_workflows


def create_app() -> FastAPI:
    """Application factory."""

    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title=settings.project_name)
    initialize_workflows()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api.api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()

