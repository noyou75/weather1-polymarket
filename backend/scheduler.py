"""
Scheduler — APScheduler job definitions.
Phase 2: market ingestion (5-minute interval).
Phase 4: NWS forecasts (6h), Open-Meteo (6h), NASA GISTEMP (12h).
Phase 5/6: signal evaluation + shadow observation (15 min).

Cloud deployment (Phase 6G):
  The scheduler is controlled by the SCHEDULER_ENABLED environment variable.
  Set SCHEDULER_ENABLED=false to disable all jobs (e.g. for debugging).
  Default: SCHEDULER_ENABLED=true (all jobs active).

  start_scheduler() and stop_scheduler() are called from main.py lifespan ONLY
  when SCHEDULER_ENABLED=true. This file does not read the env var directly.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("weather1.scheduler")
scheduler = AsyncIOScheduler(timezone="UTC")


@scheduler.scheduled_job("interval", minutes=5, id="market_ingestion", max_instances=1)
async def ingest_markets() -> None:
    """Phase 2: Poll Gamma API for open weather markets. Read-only."""
    try:
        from ingestion.polymarket import run_ingestion
        log = run_ingestion()
        logger.info("Market ingest: status=%s markets=%d %dms",
                    log.status, log.markets_stored, log.duration_ms)
    except Exception as e:
        logger.error("Market ingest error: %s", e)


@scheduler.scheduled_job("cron", hour="0,6,12,18", minute=15, id="nws_ingestion", max_instances=1)
async def ingest_nws() -> None:
    """Phase 4: NWS 7-day forecast for seeded US stations. 4× daily on model run hours."""
    try:
        from ingestion.nws import run_nws_ingestion
        log = run_nws_ingestion()
        logger.info("NWS ingest: status=%s %d/%d stations %dms",
                    log.status, log.stations_ok, log.stations_attempted, log.duration_ms)
    except Exception as e:
        logger.error("NWS ingest error: %s", e)


@scheduler.scheduled_job("cron", hour="1,7,13,19", minute=0, id="openmeteo_ingestion", max_instances=1)
async def ingest_openmeteo() -> None:
    """Phase 4: Open-Meteo 7-day forecast. 4× daily, staggered from NWS."""
    try:
        from ingestion.openmeteo import run_openmeteo_ingestion
        log = run_openmeteo_ingestion()
        logger.info("Open-Meteo ingest: status=%s %d/%d stations %dms",
                    log.status, log.stations_ok, log.stations_attempted, log.duration_ms)
    except Exception as e:
        logger.error("Open-Meteo ingest error: %s", e)


@scheduler.scheduled_job("cron", hour="3,15", minute=30, id="noaa_ingestion", max_instances=1)
async def ingest_noaa() -> None:
    """Phase 4: NASA GISTEMP global anomaly data. 2× daily (data updates ~monthly)."""
    try:
        from ingestion.noaa import run_noaa_ingestion
        log = run_noaa_ingestion()
        logger.info("GISTEMP ingest: status=%s %d records %dms",
                    log.status, log.records_stored, log.duration_ms)
    except Exception as e:
        logger.error("GISTEMP ingest error: %s", e)


# ── Phase 5: Signal evaluation ────────────────────────────────────────────────

@scheduler.scheduled_job("interval", minutes=15, id="signal_evaluation", max_instances=1)
async def evaluate_signals() -> None:
    """
    Phase 5: Run signal engine every 15 minutes.
    ANALYTICAL ONLY — no trades, no portfolio updates.
    Phase 6E: Shadow observation runs after signal evaluation.
    """
    try:
        from strategy.engine import run_signal_evaluation
        run = run_signal_evaluation()
        logger.info(
            "Signal eval: status=%s eval=%d enter=%d watch=%d skip=%d %dms",
            run.status, run.markets_evaluated,
            run.enter_candidates, run.watch_count, run.skip_count, run.duration_ms,
        )
    except Exception as e:
        logger.error("Signal eval error: %s", e)
        return

    # Phase 6E: Run shadow observation immediately after signal eval
    # NO positions. NO P&L. Shadow data only.
    try:
        from strategy.shadow_observer import run_shadow_observation
        obs = run_shadow_observation()
        logger.info(
            "Shadow obs: new=%d updated=%d snapshots=%d",
            obs["new_observations"], obs["updated_observations"], obs["snapshots_stored"],
        )
    except Exception as e:
        logger.error("Shadow observation error: %s", e)


def start_scheduler() -> None:
    """Start all scheduled jobs. Called from main.py only when SCHEDULER_ENABLED=true."""
    scheduler.start()
    jobs = [j.id for j in scheduler.get_jobs()]
    logger.info("Scheduler started — %d jobs: %s", len(jobs), jobs)


def stop_scheduler() -> None:
    """Gracefully stop scheduler on shutdown."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
