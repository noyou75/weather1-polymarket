"""
Open-Meteo ingestion — Phase 4.
Read-only. No authentication required. No private keys.

API docs: https://open-meteo.com/en/docs
Free tier: unlimited (fair use). No API key needed.

Provides 7-day daily forecast (max/min temp, precipitation) for each seeded station.
Used for Module 2 (forecast vs market probability gap) as secondary model source.

IMPORTANT NOTE on ERA5 historical:
  Open-Meteo ERA5 reanalysis is HINDCAST data — it reflects what actually happened,
  NOT what the forecast said at the time. It cannot be used as a true archived forecast
  for backtesting Module 2 accuracy. Mark all historical comparisons as [NEEDS_CHECK].
"""
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from database import engine
from models.weather import WeatherStation, WeatherForecast, WeatherIngestionLog

logger = logging.getLogger("weather1.ingestion.openmeteo")

OPENMETEO_BASE = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 2
INTER_STATION_DELAY = 0.3


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _c_to_f(c: float | None) -> float | None:
    if c is None:
        return None
    return round(c * 9 / 5 + 32, 1)


def fetch_station_forecast(station: WeatherStation, fetched_at: str) -> list[WeatherForecast]:
    """Fetch 7-day Open-Meteo forecast for one station."""
    params = {
        "latitude":        station.latitude,
        "longitude":       station.longitude,
        "daily":           "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "timezone":        station.timezone,
        "forecast_days":   7,
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = httpx.get(OPENMETEO_BASE, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            break
        except httpx.TimeoutException:
            logger.warning("Open-Meteo timeout attempt %d for %s", attempt + 1, station.station_id)
            if attempt < MAX_RETRIES:
                time.sleep(1.5)
            else:
                return []
        except Exception as e:
            logger.error("Open-Meteo error for %s: %s", station.station_id, e)
            return []

    try:
        daily = data["daily"]
        dates = daily["time"]
        max_c = daily.get("temperature_2m_max", [])
        min_c = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        pop = daily.get("precipitation_probability_max", [])
    except Exception as e:
        logger.error("Failed to parse Open-Meteo response for %s: %s", station.station_id, e)
        return []

    records: list[WeatherForecast] = []
    for i, date in enumerate(dates):
        mx_c = max_c[i] if i < len(max_c) else None
        mn_c = min_c[i] if i < len(min_c) else None
        pr   = precip[i] if i < len(precip) else None
        pp   = pop[i] if i < len(pop) else None

        records.append(WeatherForecast(
            station_id        = station.station_id,
            source            = "openmeteo",
            forecast_date     = date,
            period_label      = f"Day {i+1}",
            temperature_max_c = mx_c,
            temperature_min_c = mn_c,
            temperature_max_f = _c_to_f(mx_c),
            temperature_min_f = _c_to_f(mn_c),
            precipitation_mm  = pr,
            prob_precipitation = float(pp) if pp is not None else None,
            fetched_at        = fetched_at,
            valid_from        = date,
        ))
    return records


def run_openmeteo_ingestion() -> WeatherIngestionLog:
    """Fetch Open-Meteo forecasts for all seeded stations."""
    t_start = time.monotonic()
    log = WeatherIngestionLog(run_at=_now_iso(), source="openmeteo", status="error")

    stations_ok = 0
    records_stored = 0
    errors: list[str] = []
    fetched_at = _now_iso()

    with Session(engine) as s:
        stations = s.exec(select(WeatherStation)).all()

    for station in stations:
        try:
            forecasts = fetch_station_forecast(station, fetched_at)
            if not forecasts:
                errors.append(f"{station.station_id}: no data")
                continue
            with Session(engine, expire_on_commit=False) as s:
                for fc in forecasts:
                    s.add(fc)
                s.commit()
            records_stored += len(forecasts)
            stations_ok += 1
            logger.info("Open-Meteo %s: %d days stored", station.station_id, len(forecasts))
        except Exception as e:
            errors.append(f"{station.station_id}: {e}")
        time.sleep(INTER_STATION_DELAY)

    log.stations_attempted = len(stations)
    log.stations_ok = stations_ok
    log.records_stored = records_stored
    log.status = "ok" if not errors else ("partial" if stations_ok > 0 else "error")
    log.error_message = "; ".join(errors[:5]) if errors else None
    log.duration_ms = int((time.monotonic() - t_start) * 1000)

    with Session(engine, expire_on_commit=False) as s:
        s.add(log)
        s.commit()

    logger.info("Open-Meteo ingestion: %s | %d/%d stations | %d records | %dms",
                log.status, stations_ok, len(stations), records_stored, log.duration_ms)
    return log
