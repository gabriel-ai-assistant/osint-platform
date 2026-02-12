"""FastAPI application — OSINT Intelligence Platform API."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from osint.api.routes import health, investigate, lookup, photos, providers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Load .env if present (for local development)
try:
    from dotenv import load_dotenv

    # Walk up to find .env
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("Loaded .env from %s", env_path)
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    logger.info("🚀 OSINT Intelligence Platform starting up...")
    yield
    logger.info("🛑 OSINT Intelligence Platform shutting down...")


app = FastAPI(
    title="OSINT Intelligence Platform",
    description="Enterprise-grade open source intelligence aggregation and analysis",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow all in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(lookup.router, prefix="/api", tags=["lookup"])
app.include_router(investigate.router, prefix="/api", tags=["investigate"])
app.include_router(photos.router, prefix="/api", tags=["photos"])

# Also mount under /osint/api for nginx proxy path
app.include_router(health.router, prefix="/osint/api", tags=["health"])
app.include_router(providers.router, prefix="/osint/api", tags=["providers"])
app.include_router(lookup.router, prefix="/osint/api", tags=["lookup"])
app.include_router(investigate.router, prefix="/osint/api", tags=["investigate"])
app.include_router(photos.router, prefix="/osint/api", tags=["photos"])

# Serve static frontend in production
_web_dist = Path(__file__).resolve().parent.parent.parent / "web" / "dist"
if _web_dist.exists():
    # Mount assets directory
    _assets = _web_dist / "assets"
    if _assets.exists():
        app.mount("/osint/assets", StaticFiles(directory=str(_assets)), name="osint-assets")
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    from fastapi.responses import FileResponse

    @app.get("/osint/{rest_of_path:path}")
    async def serve_osint_spa(rest_of_path: str) -> FileResponse:
        """Serve the SPA under /osint/ path."""
        # Try to serve the exact file first
        file_path = _web_dist / rest_of_path
        if rest_of_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for SPA routing
        return FileResponse(str(_web_dist / "index.html"))

    @app.get("/")
    async def redirect_root() -> FileResponse:
        """Serve index.html at root."""
        return FileResponse(str(_web_dist / "index.html"))

    logger.info("Serving frontend from %s", _web_dist)
else:
    logger.info("No frontend build found at %s — API-only mode", _web_dist)
