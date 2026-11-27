"""Compose the HTTP application."""

from fastapi import FastAPI

from data_model_auditor import __version__
from data_model_auditor.bootstrap.settings import Settings
from data_model_auditor.infrastructure.http.errors import register_exception_handlers
from data_model_auditor.infrastructure.http.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the versioned API. The caller supplies settings in tests."""
    resolved = Settings.from_environ() if settings is None else settings
    app = FastAPI(title="Data Model Auditor", version=__version__)
    app.state.settings = resolved
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
