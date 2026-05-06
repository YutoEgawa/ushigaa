from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ウシガー API",
        version="0.1.0",
        description="Neutral API for Japanese Diet legislator data.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix=settings.api_prefix)
    return app


app = create_app()
