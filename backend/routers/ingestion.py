"""
Ingestion router — Phase 2.
GET  /ingestion/status  — last run info and health
POST /ingestion/run-once — trigger manual fetch (local dev only, read-only)
GET  /ingestion/logs    — recent ingestion log entries
"""
import logging
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models.ingestion_logs import IngestionLog

logger = logging.getLogger("weather1.routers.ingestion")
router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.get("/status", summary="Ingestion pipeline health and last run stats")
def ingestion_status():
    """Returns health info about the data ingestion pipeline."""
    from ingestion.polymarket import get_ingestion_status
    return get_ingestion_status()


@router.post("/run-once", summary="Manually trigger one ingestion cycle (local dev only)")
def run_once():
    """
    Triggers a single read-only fetch from Gamma API.
    Safe for local development. No write calls to Polymarket.
    No authentication. No order placement.
    """
    logger.info("Manual ingestion triggered via /ingestion/run-once")
    from ingestion.polymarket import run_ingestion
    log = run_ingestion()
    return {
        "status": log.status,
        "events_fetched": log.events_fetched,
        "markets_fetched": log.markets_fetched,
        "markets_stored": log.markets_stored,
        "prices_stored": log.prices_stored,
        "duration_ms": log.duration_ms,
        "error": log.error_message,
        "run_at": log.run_at,
    }


@router.get("/logs", summary="Recent ingestion log entries")
def ingestion_logs(limit: int = 20, session: Session = Depends(get_session)):
    logs = session.exec(
        select(IngestionLog).order_by(IngestionLog.id.desc()).limit(limit)  # type: ignore[arg-type]
    ).all()
    return {
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "run_at": l.run_at,
                "status": l.status,
                "events_fetched": l.events_fetched,
                "markets_fetched": l.markets_fetched,
                "markets_stored": l.markets_stored,
                "duration_ms": l.duration_ms,
                "error": l.error_message,
            }
            for l in logs
        ],
    }
