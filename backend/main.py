"""
Weather1 — FastAPI Backend
Phase 6G: Cloud-ready configuration for Railway deployment.

Local start:   uv run uvicorn main:app --reload --port 8000
Railway start: uv run uvicorn main:app --host 0.0.0.0 --port $PORT

Environment variables:
  PORT              — TCP port (default 8000; Railway sets this automatically)
  WEATHER1_DB_PATH  — SQLite file path (default: local data/weather1.db)
                      Railway: set to /data/weather1.db (persistent Volume)
  SCHEDULER_ENABLED — "true"|"false" (default true); set false to disable
  CORS_ORIGINS      — comma-separated allowed origins
                      default: http://localhost:3000
                      Railway: add your frontend URL
  APP_ENV           — "development"|"production" (default development)
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_db_and_tables
from scheduler import start_scheduler, stop_scheduler
from routers import (
    markets, signals, portfolio, risk, wallets, backtest,
    logs, ingestion, prices, weather, settlement, shadow,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("weather1")

# ── Environment variables ─────────────────────────────────────────────────────
APP_ENV            = os.getenv("APP_ENV", "development")
SCHEDULER_ENABLED  = os.getenv("SCHEDULER_ENABLED", "true").strip().lower() == "true"
_cors_raw          = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS       = [o.strip() for o in _cors_raw.split(",") if o.strip()]

# Always add localhost for local dev when other origins are set
if "http://localhost:3000" not in CORS_ORIGINS:
    CORS_ORIGINS.append("http://localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Weather1 backend starting — Phase 6G (cloud-ready) | env=%s | scheduler=%s",
        APP_ENV, SCHEDULER_ENABLED,
    )
    create_db_and_tables()

    from ingestion.seed_stations import seed_stations_if_empty
    seeded = seed_stations_if_empty()
    if seeded:
        logger.info("Seeded %d weather stations", seeded)

    if SCHEDULER_ENABLED:
        start_scheduler()
        logger.info("Scheduler started (SCHEDULER_ENABLED=true)")
    else:
        logger.warning("Scheduler DISABLED (SCHEDULER_ENABLED=false) — shadow monitoring inactive")

    yield

    if SCHEDULER_ENABLED:
        stop_scheduler()
    logger.info("Weather1 backend stopped")


app = FastAPI(
    title="Weather1 — Polymarket Weather Edge Engine",
    description=(
        "Phase 6G — Cloud-ready deployment. "
        "No private keys. No real orders. No Polymarket write calls. "
        "Shadow monitoring: live signal price observation (no positions)."
    ),
    version="0.6G-phase6g",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # allow any Vercel preview URL
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(markets.router)
app.include_router(signals.router)
app.include_router(portfolio.router)
app.include_router(risk.router)
app.include_router(wallets.router)
app.include_router(backtest.router)
app.include_router(logs.router)
app.include_router(ingestion.router)
app.include_router(prices.router)
app.include_router(weather.router)
app.include_router(settlement.router)
app.include_router(shadow.router)


@app.get("/", tags=["Health"])
def root():
    from database import _db_path
    return {
        "project":      "Weather1 — Polymarket Weather Edge Engine",
        "phase":        "6G — Cloud-ready shadow monitoring",
        "env":          APP_ENV,
        "scheduler":    SCHEDULER_ENABLED,
        "db_path":      str(_db_path),
        "cors_origins": CORS_ORIGINS,
        "real_orders":  False,
        "private_keys": False,
        "write_calls":  False,
        "docs":         "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    """Railway health check endpoint."""
    from database import engine
    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status":    "ok" if db_ok else "degraded",
        "db":        "ok" if db_ok else "error",
        "scheduler": SCHEDULER_ENABLED,
        "phase":     "6G",
    }
