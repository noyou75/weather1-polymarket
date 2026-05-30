"""
NWS (National Weather Service) ingestion — Phase 4.
Read-only. No authentication. No private keys.

Endpoint: https://api.weather.gov/points/{lat},{lon}  → forecast URL
          {forecast_url}                              → 14-period forecast

NWS requires a User-Agent header identifying the application.
NWS API Terms: https://www.weather.gov/documentation/services-web-api
"""
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from database import engine
from models.weather import WeatherStation, WeatherForecast, WeatherIngestionLog
from ingestion.stations import STATIONS

logger = logging.getLogger("weather1.ingestion.nws")

NWS_BASE = "https://api.weather.gov"
REQUEST_TIMEOUT = 12.0
MAX_RETRIES = 2
INTER_STATION_DELAY = 0.8   # NWS rate limits; be polite

# NWS requires a descriptive User-Agent (they block generic ones)
HEADERS = {
    "User-Agent": "Weather1/0.4 (Polymarket weather research tool; github.com/weather1)",
    "Accept": "application/geo+json",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f_to_c(f: float | None) -> float | None:
    if f is None:
        return None
    return round((f - 32) * 5 / 9, 2)


def _get_with_retry(url: str) -> httpx.Response | None:
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = httpx.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
            if r.status_code == 200:
                return r
            logger.warning("NWS %s returned %d", url[-60:], r.status_code)
            return None
        except httpx.TimeoutException:
            logger.warning("NWS timeout attempt %d: %s", attempt + 1, url[-60:])
        except Exception as e:
            logger.error("NWS request error: %s — %s", url[-60:], e)
            return None
        if attempt < MAX_RETRIES:
            time.sleep(1.5 * (attempt + 1))
    return None


def _resolve_grid(station: WeatherStation) -> str | None:
    """
    Call /points/{lat},{lon} to get the forecast URL.
    Caches result in the WeatherStation record.
    Returns forecast URL or None on failure.
    """
    if station.nws_forecast_url:
        return station.nws_forecast_url

    url = f"{NWS_BASE}/points/{station.latitude},{station.longitude}"
    r = _get_with_retry(url)
    if not r:
        return None
    try:
        props = r.json()["properties"]
        forecast_url = props["forecast"]
        grid_id = props["gridId"]
        grid_x = props["gridX"]
        grid_y = props["gridY"]

        # Cache in DB
        with Session(engine, expire_on_commit=False) as s:
            st = s.exec(select(WeatherStation).where(
                WeatherStation.station_id == station.station_id
            )).first()
            if st:
                st.nws_forecast_url = forecast_url
                st.nws_grid_id = grid_id
                st.nws_grid_x = int(grid_x)
                st.nws_grid_y = int(grid_y)
                s.add(st)
                s.commit()
        return forecast_url
    except Exception as e:
        logger.error("Failed to parse NWS /points response: %s", e)
        return None


def fetch_station_forecast(station: WeatherStation, fetched_at: str) -> list[WeatherForecast]:
    """Fetch 7-day NWS forecast for one station. Returns list of WeatherForecast objects."""
    forecast_url = _resolve_grid(station)
    if not forecast_url:
        logger.warning("No forecast URL for %s — skipping", station.station_id)
        return []

    r = _get_with_retry(forecast_url)
    if not r:
        return []

    try:
        periods = r.json()["properties"]["periods"]
    except Exception as e:
        logger.error("Failed to parse NWS forecast for %s: %s", station.station_id, e)
        return []

    records: list[WeatherForecast] = []
    for p in periods:
        try:
            temp_f = float(p.get("temperature", 0))
            is_daytime = p.get("isDaytime", True)
            start = p.get("startTime", "")
            date_str = start[:10] if len(start) >= 10 else ""
            pop = p.get("probabilityOfPrecipitation", {})
            pop_val = pop.get("value") if isinstance(pop, dict) else None

            records.append(WeatherForecast(
                station_id       = station.station_id,
                source           = "nws",
                forecast_date    = date_str,
                period_label     = p.get("name", ""),
                temperature_max_f = temp_f if is_daytime else None,
                temperature_min_f = temp_f if not is_daytime else None,
                temperature_max_c = _f_to_c(temp_f) if is_daytime else None,
                temperature_min_c = _f_to_c(temp_f) if not is_daytime else None,
                wind_speed_text  = p.get("windSpeed"),
                short_forecast   = p.get("shortForecast"),
                prob_precipitation = float(pop_val) if pop_val is not None else None,
                fetched_at       = fetched_at,
                valid_from       = start,
            ))
        except Exception as e:
            logger.warning("Could not parse NWS period for %s: %s", station.station_id, e)

    return records


def run_nws_ingestion() -> WeatherIngestionLog:
    """Fetch NWS forecasts for all seeded stations. Returns a log record."""
    t_start = time.monotonic()
    log = WeatherIngestionLog(
        run_at=_now_iso(), source="nws", status="error"
    )

    stations_ok = 0
    records_stored = 0
    errors: list[str] = []
    fetched_at = _now_iso()

    with Session(engine, expire_on_commit=False) as s:
        stations = s.exec(select(WeatherStation)).all()

    for station in stations:
        try:
            forecasts = fetch_station_forecast(station, fetched_at)
            if not forecasts:
                errors.append(f"{station.station_id}: no forecast returned")
                time.sleep(INTER_STATION_DELAY)
                continue

            with Session(engine, expire_on_commit=False) as s:
                for fc in forecasts:
                    s.add(fc)
                s.commit()

            records_stored += len(forecasts)
            stations_ok += 1
            logger.info("NWS %s: %d periods stored", station.station_id, len(forecasts))
        except Exception as e:
            errors.append(f"{station.station_id}: {e}")
            logger.error("NWS station %s failed: %s", station.station_id, e)
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

    logger.info("NWS ingestion: %s | %d/%d stations | %d records | %dms",
                log.status, stations_ok, len(stations), records_stored, log.duration_ms)
    return log
