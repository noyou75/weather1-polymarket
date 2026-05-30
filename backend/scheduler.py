"""
Scheduler — APScheduler job definitions.
Phase 6H: Staggered cron scheduling to prevent job collisions on Railway.

Job timing (all UTC, cron-absolute so Railway always fires at the same wall-clock time):

  :00,:05,:10,:15,:20,:25,:30,:35,:40,:45,:50,:55  — market ingestion  (~5–8s)
  :03,:18,:33,:48                                  — signal eval + shadow obs  (~1–3s total)
  0/6/12/18:15                                     — NWS forecast (4×/day, ~90s)
  1/7/13/19:00                                     — Open-Meteo (4×/day, ~10s)
  3/15:30                                          — NASA GISTEMP (2×/day, ~5s)

Signal evaluation runs 3 minutes AFTER market ingestion, so markets are fresh
and ingestion is guaranteed complete before signals score them.

Shadow observation runs INSIDE the signal evaluation job, immediately after
signal eval completes — no separate schedule needed.

misfire_grace_time=30s: if Railway is temporarily busy and fires a job up to
30 seconds late, it still runs instead of being skipped entirely.
coalesce=True: if multiple missed firings stacked up, run only once on recovery.

Cloud deployment (Phase 6G/6H):
  SCHEDULER_ENABLED env var controls whether scheduler starts at all.
  Set SCHEDULER_ENABLED=false to disable (e.g. for debugging).
  Default: SCHEDULER_ENABLED=true.
"""
import logging
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("weather1.scheduler")

# ── Scheduler configuration ───────────────────────────────────────────────────
scheduler = AsyncIOScheduler(
    timezone="UTC",
    job_defaults={
        "misfire_grace_time": 30,   # fire if ≤30s late (handles Railway cold-start lag)
        "coalesce": True,            # collapse missed stacked firings into one
        "max_instances": 1,          # never run the same job twice simultaneously
    },
)

# ── Market ingestion — every 5 min ────────────────────────────────────────────
# Fires at :00, :05, :10, :15, :20, :25, :30, :35, :40, :45, :50, :55
# Using cron (not interval) so Railway always fires at the SAME absolute minutes
# regardless of when the process started.

@scheduler.scheduled_job(
    "cron",
    minute="0,5,10,15,20,25,30,35,40,45,50,55",
    id="market_ingestion",
)
async def ingest_markets() -> None:
    """Phase 2: Poll Gamma API for open weather markets. Read-only. No write calls."""
    t0 = time.monotonic()
    logger.info("[scheduler] market_ingestion START")
    try:
        from ingestion.polymarket import run_ingestion
        log = run_ingestion()
        logger.info(
            "[scheduler] market_ingestion END: status=%s markets=%d duration=%dms total=%.1fs",
            log.status, log.markets_stored, log.duration_ms, time.monotonic() - t0,
        )
    except Exception as e:
        logger.error("[scheduler] market_ingestion ERROR: %s (%.1fs)", e, time.monotonic() - t0)


# ── Signal evaluation + shadow observation — every 15 min, offset +3 min ──────
# Fires at :03, :18, :33, :48 — guaranteed to start AFTER market ingestion
# (which fires at :00/:05/:10/:15 and takes ~5–8s, so it's done by :01 latest).
# Shadow observation is chained INSIDE this job so it always runs after signals.

@scheduler.scheduled_job(
    "cron",
    minute="3,18,33,48",
    id="signal_and_shadow",
)
async def evaluate_signals_and_shadow() -> None:
    """
    Phase 5/6: Signal evaluation then shadow observation.
    ANALYTICAL ONLY — no trades, no positions, no portfolio updates.
    Fires 3 minutes after market ingestion to use freshly updated prices.
    """
    # ── Signal evaluation ──────────────────────────────────────────────────────
    t0 = time.monotonic()
    logger.info("[scheduler] signal_evaluation START")
    try:
        from strategy.engine import run_signal_evaluation
        run = run_signal_evaluation()
        logger.info(
            "[scheduler] signal_evaluation END: status=%s eval=%d enter=%d watch=%d skip=%d %dms total=%.1fs",
            run.status, run.markets_evaluated, run.enter_candidates,
            run.watch_count, run.skip_count, run.duration_ms, time.monotonic() - t0,
        )
    except Exception as e:
        logger.error("[scheduler] signal_evaluation ERROR: %s (%.1fs)", e, time.monotonic() - t0)
        # Shadow still runs even if signal eval partially fails

    # ── Shadow observation — runs immediately after signal eval ────────────────
    # NO positions. NO P&L. Observation data only.
    t1 = time.monotonic()
    logger.info("[scheduler] shadow_observation START")
    try:
        from strategy.shadow_observer import run_shadow_observation
        obs = run_shadow_observation()
        logger.info(
            "[scheduler] shadow_observation END: new=%d updated=%d snaps=%d status=%s total=%.1fs",
            obs.get("new_observations", 0),
            obs.get("updated_observations", 0),
            obs.get("snapshots_stored", 0),
            obs.get("status", "?"),
            time.monotonic() - t1,
        )
    except Exception as e:
        logger.error("[scheduler] shadow_observation ERROR: %s (%.1fs)", e, time.monotonic() - t1)


# ── NWS 7-day forecast — 4× daily at 0:15, 6:15, 12:15, 18:15 UTC ────────────
# Offset by 15 min into model-run hours so data is available.
# Finishes in ~60–90s, well before signal eval fires at :18 and :33.

@scheduler.scheduled_job(
    "cron",
    hour="0,6,12,18",
    minute=15,
    id="nws_ingestion",
)
async def ingest_nws() -> None:
    """Phase 4: NWS 7-day forecast for seeded US stations. 4× daily."""
    t0 = time.monotonic()
    logger.info("[scheduler] nws_ingestion START")
    try:
        from ingestion.nws import run_nws_ingestion
        log = run_nws_ingestion()
        logger.info(
            "[scheduler] nws_ingestion END: status=%s %d/%d stations %dms total=%.1fs",
            log.status, log.stations_ok, log.stations_attempted, log.duration_ms, time.monotonic() - t0,
        )
    except Exception as e:
        logger.error("[scheduler] nws_ingestion ERROR: %s (%.1fs)", e, time.monotonic() - t0)


# ── Open-Meteo forecast — 4× daily at 1:00, 7:00, 13:00, 19:00 UTC ──────────
# Staggered 1 hour from NWS to avoid overlap with signal eval.

@scheduler.scheduled_job(
    "cron",
    hour="1,7,13,19",
    minute=0,
    id="openmeteo_ingestion",
)
async def ingest_openmeteo() -> None:
    """Phase 4: Open-Meteo 7-day forecast. 4× daily, staggered from NWS."""
    t0 = time.monotonic()
    logger.info("[scheduler] openmeteo_ingestion START")
    try:
        from ingestion.openmeteo import run_openmeteo_ingestion
        log = run_openmeteo_ingestion()
        logger.info(
            "[scheduler] openmeteo_ingestion END: status=%s %d/%d stations %dms total=%.1fs",
            log.status, log.stations_ok, log.stations_attempted, log.duration_ms, time.monotonic() - t0,
        )
    except Exception as e:
        logger.error("[scheduler] openmeteo_ingestion ERROR: %s (%.1fs)", e, time.monotonic() - t0)


# ── NASA GISTEMP — 2× daily at 3:30 and 15:30 UTC ────────────────────────────
# Data updates monthly; twice daily is more than enough.

@scheduler.scheduled_job(
    "cron",
    hour="3,15",
    minute=30,
    id="noaa_ingestion",
)
async def ingest_noaa() -> None:
    """Phase 4: NASA GISTEMP global anomaly data. 2× daily."""
    t0 = time.monotonic()
    logger.info("[scheduler] noaa_ingestion START")
    try:
        from ingestion.noaa import run_noaa_ingestion
        log = run_noaa_ingestion()
        logger.info(
            "[scheduler] noaa_ingestion END: status=%s %d records %dms total=%.1fs",
            log.status, log.records_stored, log.duration_ms, time.monotonic() - t0,
        )
    except Exception as e:
        logger.error("[scheduler] noaa_ingestion ERROR: %s (%.1fs)", e, time.monotonic() - t0)


# ── Settlement source verification — daily at 4:00 UTC ───────────────────────
# Lightweight; just re-confirms NASA GISTEMP as settlement source.

@scheduler.scheduled_job(
    "cron",
    hour=4,
    minute=0,
    id="settlement_verification",
)
async def verify_settlement() -> None:
    """Phase 6D: Verify settlement source for temperature markets. 1× daily."""
    t0 = time.monotonic()
    try:
        from ingestion.settlement_sources import run_settlement_verification
        result = run_settlement_verification()
        logger.info(
            "[scheduler] settlement_verification: sources=%s outcomes=%d total=%.1fs",
            result.get("sources_verified", []), result.get("outcomes_stored", 0), time.monotonic() - t0,
        )
    except Exception as e:
        logger.error("[scheduler] settlement_verification ERROR: %s (%.1fs)", e, time.monotonic() - t0)


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def start_scheduler() -> None:
    """Start all scheduled jobs. Called from main.py only when SCHEDULER_ENABLED=true."""
    scheduler.start()
    jobs = scheduler.get_jobs()
    logger.info("Scheduler started — %d jobs:", len(jobs))
    for job in jobs:
        logger.info(
            "  %-30s  next_run=%s",
            job.id,
            job.next_run_time.strftime("%H:%M:%S UTC") if job.next_run_time else "unknown",
        )


def stop_scheduler() -> None:
    """Gracefully stop scheduler on shutdown."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


def get_scheduler_status() -> dict:
    """Return current scheduler state and next run times for all jobs."""
    if not scheduler.running:
        return {"running": False, "jobs": []}
    jobs = []
    for job in scheduler.get_jobs():
        nrt = job.next_run_time
        jobs.append({
            "id":            job.id,
            "trigger":       str(job.trigger),
            "next_run_utc":  nrt.strftime("%Y-%m-%dT%H:%M:%SZ") if nrt else None,
            "max_instances": job.max_instances,
        })
    return {
        "running":    True,
        "job_count":  len(jobs),
        "timezone":   "UTC",
        "stagger_note": (
            "Phase 6H: market ingestion at :00/:05/..., "
            "signal+shadow at :03/:18/:33/:48 (3-min offset). "
            "misfire_grace_time=30s, coalesce=True."
        ),
        "jobs": jobs,
    }
