"""
NOAA / NASA global temperature anomaly ingestion — Phase 4.
Read-only. No authentication required. No private keys.

Data source: NASA GISS Surface Temperature Analysis (GISTEMP v4)
CSV URL: https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv
Baseline: 1951–1980 global average

Column format:
  Year, Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec, J-D, D-N, DJF, MAM, JJA, SON
  Anomaly in °C above 1951–1980 mean. '***' = not yet published.

SETTLEMENT NOTE [NEEDS_CHECK]:
  Polymarket 'hottest month on record' and 'Global Heat Increase' markets
  may use NOAA GlobalTemp or another dataset as their official resolution source.
  NASA GISTEMP v4 is one of the main global temperature datasets but may NOT be
  the exact dataset cited in Polymarket market resolution criteria.
  Do NOT assume this data matches Polymarket settlement without verification.

All-time monthly records: used to compute rank for 'hottest month on record' market types.
"""
import csv
import io
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from database import engine
from models.weather import GlobalTemperatureAnomaly, WeatherIngestionLog

logger = logging.getLogger("weather1.ingestion.noaa")

GISTEMP_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
REQUEST_TIMEOUT = 20.0
MAX_RETRIES = 2

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# v1.1 (Phase 6C): Extended to 2000 to provide better prior context for annual rank signals.
# Previous value was 2020 — caused 2020 false positives due to no prior-year context.
# Phase 0 Phase 6B diagnosis: "require >= 3 prior full years before generating signal".
MIN_YEAR = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_anomaly(raw: str) -> float | None:
    """Parse an anomaly value, returning None for '***' (not yet published)."""
    raw = raw.strip()
    if raw in ("***", "", "****"):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def fetch_gistemp_data() -> list[dict]:
    """
    Download and parse NASA GISTEMP v4 global anomaly CSV.
    Returns list of dicts: {year, month, month_name, anomaly_c}
    Only returns rows where anomaly_c is not None (i.e., published data).
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = httpx.get(GISTEMP_URL, timeout=REQUEST_TIMEOUT, follow_redirects=True)
            r.raise_for_status()
            break
        except httpx.TimeoutException:
            logger.warning("GISTEMP timeout attempt %d", attempt + 1)
            if attempt < MAX_RETRIES:
                time.sleep(2.0)
            else:
                raise
        except Exception as e:
            logger.error("GISTEMP fetch error: %s", e)
            raise

    lines = r.text.strip().splitlines()
    # Skip header lines until we find the column header row
    data_lines = []
    header_found = False
    for line in lines:
        if line.startswith("Year"):
            header_found = True
            continue
        if header_found and line.strip():
            data_lines.append(line)

    if not header_found:
        raise ValueError("GISTEMP CSV header 'Year,...' not found")

    records = []
    reader = csv.reader(data_lines)
    for row in reader:
        if not row or not row[0].strip().isdigit():
            continue
        year = int(row[0].strip())
        if year < MIN_YEAR:
            continue
        for month_idx, month_name in enumerate(MONTH_NAMES):
            col = month_idx + 1   # columns: Year=0, Jan=1 ... Dec=12
            if col >= len(row):
                continue
            val = _parse_anomaly(row[col])
            if val is None:
                continue
            records.append({
                "year": year,
                "month": month_idx + 1,
                "month_name": month_name,
                "anomaly_c": val,
            })

    return records


def _compute_monthly_ranks(records: list[dict]) -> dict[tuple[int, int], int]:
    """
    For each (year, month) in records, compute all-time rank among same calendar month.
    Rank 1 = warmest (highest anomaly).
    Uses ALL available data from MIN_YEAR onwards (limited history, so rank is approximate).
    """
    by_month: dict[int, list[tuple[float, int, int]]] = {}
    for r in records:
        m = r["month"]
        if m not in by_month:
            by_month[m] = []
        by_month[m].append((r["anomaly_c"], r["year"], r["month"]))

    ranks: dict[tuple[int, int], int] = {}
    for m, entries in by_month.items():
        sorted_entries = sorted(entries, reverse=True)
        for rank, (_, year, month) in enumerate(sorted_entries, start=1):
            ranks[(year, month)] = rank
    return ranks


def run_noaa_ingestion() -> WeatherIngestionLog:
    """Fetch and store NASA GISTEMP global temperature anomaly data."""
    t_start = time.monotonic()
    log = WeatherIngestionLog(run_at=_now_iso(), source="nasa_gistemp", status="error")

    fetched_at = _now_iso()

    try:
        raw_records = fetch_gistemp_data()
        logger.info("GISTEMP: parsed %d published monthly anomaly records", len(raw_records))
    except Exception as e:
        log.error_message = f"Fetch failed: {e}"
        log.duration_ms = int((time.monotonic() - t_start) * 1000)
        with Session(engine, expire_on_commit=False) as s:
            s.add(log)
            s.commit()
        return log

    if not raw_records:
        log.status = "ok"
        log.error_message = "No published data returned (all months may be '***')"
        log.duration_ms = int((time.monotonic() - t_start) * 1000)
        with Session(engine, expire_on_commit=False) as s:
            s.add(log)
            s.commit()
        return log

    # Compute relative monthly rankings (approximate — limited history from MIN_YEAR)
    ranks = _compute_monthly_ranks(raw_records)

    stored = 0
    errors: list[str] = []

    with Session(engine, expire_on_commit=False) as s:
        for rec in raw_records:
            try:
                year, month = rec["year"], rec["month"]
                rank = ranks.get((year, month))
                is_record = (rank == 1)

                existing = s.exec(
                    select(GlobalTemperatureAnomaly).where(
                        GlobalTemperatureAnomaly.year == year,
                        GlobalTemperatureAnomaly.month == month,
                    )
                ).first()

                if existing:
                    existing.anomaly_c = rec["anomaly_c"]
                    existing.all_time_rank = rank
                    existing.is_record_warmest = is_record
                    existing.fetched_at = fetched_at
                    s.add(existing)
                else:
                    s.add(GlobalTemperatureAnomaly(
                        year             = year,
                        month            = month,
                        month_name       = rec["month_name"],
                        anomaly_c        = rec["anomaly_c"],
                        source           = "nasa_gistemp_v4",
                        baseline_period  = "1951-1980",
                        all_time_rank    = rank,
                        is_record_warmest = is_record,
                        fetched_at       = fetched_at,
                    ))
                stored += 1
            except Exception as e:
                errors.append(f"{rec.get('year')}-{rec.get('month')}: {e}")

        try:
            s.commit()
        except Exception as e:
            errors.append(f"commit: {e}")

    log.stations_attempted = 1   # one global source
    log.stations_ok = 1 if stored > 0 else 0
    log.records_stored = stored
    log.status = "ok" if not errors else ("partial" if stored > 0 else "error")
    log.error_message = "; ".join(errors[:5]) if errors else None
    log.duration_ms = int((time.monotonic() - t_start) * 1000)

    with Session(engine, expire_on_commit=False) as s:
        s.add(log)
        s.commit()

    logger.info("GISTEMP ingestion: %s | %d records | %dms", log.status, stored, log.duration_ms)
    return log
