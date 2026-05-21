"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import init_db
from backend.scheduler import start_scheduler, stop_scheduler
from backend.routers import neos, alerts
from backend.services.nasa_client import close_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting background scheduler...")
    start_scheduler()

    # Trigger an immediate first poll so data is available on first request
    from backend.scheduler import _poll_job
    await _poll_job()

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    stop_scheduler()
    await close_client()
    logger.info("Application shut down cleanly")


app = FastAPI(
    title="NEO Risk & Trajectory Dashboard API",
    description=(
        "Real-time Near-Earth Object tracking, orbital mechanics, "
        "Monte Carlo trajectory uncertainty, and impact risk scoring."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(neos.router)
app.include_router(alerts.router)


@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
