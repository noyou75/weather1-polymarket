"""
Weather router — Phase 4.
Serves weather forecast, observations, and global anomaly data from SQLite.
All data is read-only. No private keys. No real orders.
"""
import logging
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models.weather import WeatherStation, WeatherForecast, GlobalTemperatureAnomaly, WeatherIngestionLog

logger = logging.getLogger("weather1.routers.weather")
router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/status", summary="Weather ingestion pipeline status")
def weather_status(session: Session = Depends(get_session)):
    """Returns status for each weather data source."""
    sources = ["nws", "openmeteo", "nasa_gistemp"]
    result: dict = {"sources": {}}

    for src in sources:
        logs = session.exec(
            select(WeatherIngestionLog)
            .where(WeatherIngestionLog.source == src)
            .order_by(WeatherIngestionLog.id.desc())  # type: ignore[arg-type]
            .limit(1)
        ).all()
        last = logs[0] if logs else None
        result["sources"][src] = {
            "last_run": last.run_at if last else None,
            "status": last.status if last else "never_run",
            "records_stored": last.records_stored if last else 0,
            "last_error": last.error_message if last else None,
            "duration_ms": last.duration_ms if last else 0,
        }

    # Station count
    stations = session.exec(select(WeatherStation)).all()
    result["stations_seeded"] = len(stations)

    # Forecast count
    forecasts = session.exec(select(WeatherForecast)).all()
    result["forecast_records"] = len(forecasts)

    # Anomaly count
    anomalies = session.exec(select(GlobalTemperatureAnomaly)).all()
    result["anomaly_records"] = len(anomalies)

    return result


@router.get("/stations", summary="Seeded weather station list")
def list_stations(session: Session = Depends(get_session)):
    stations = session.exec(select(WeatherStation).order_by(WeatherStation.id)).all()  # type: ignore[arg-type]
    return {
        "count": len(stations),
        "stations": [
            {
                "station_id":     s.station_id,
                "name":           s.name,
                "city":           s.city,
                "state":          s.state,
                "latitude":       s.latitude,
                "longitude":      s.longitude,
                "timezone":       s.timezone,
                "nws_grid":       f"{s.nws_grid_id}/{s.nws_grid_x},{s.nws_grid_y}" if s.nws_grid_id else None,
                "notes":          s.notes,
            }
            for s in stations
        ],
    }


@router.get("/forecasts/latest", summary="Latest forecast per station per source")
def latest_forecasts(
    station_id: str = "",
    source: str = "",
    session: Session = Depends(get_session),
):
    stmt = select(WeatherForecast).order_by(WeatherForecast.id.desc())  # type: ignore[arg-type]
    forecasts = session.exec(stmt).all()

    # Deduplicate: one row per (station_id, source, forecast_date)
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for f in forecasts:
        key = (f.station_id, f.source, f.forecast_date)
        if key in seen:
            continue
        if station_id and f.station_id != station_id:
            continue
        if source and f.source != source:
            continue
        seen.add(key)
        unique.append({
            "station_id":       f.station_id,
            "source":           f.source,
            "forecast_date":    f.forecast_date,
            "period_label":     f.period_label,
            "temp_max_f":       f.temperature_max_f,
            "temp_min_f":       f.temperature_min_f,
            "temp_max_c":       f.temperature_max_c,
            "temp_min_c":       f.temperature_min_c,
            "precipitation_mm": f.precipitation_mm,
            "prob_precip_pct":  f.prob_precipitation,
            "wind":             f.wind_speed_text,
            "short_forecast":   f.short_forecast,
            "fetched_at":       f.fetched_at,
        })

    return {
        "count": len(unique),
        "note": "Weather data only — no signals yet. Phase 5 will compare these to Polymarket prices.",
        "forecasts": unique,
    }


@router.get("/global-anomalies", summary="Global temperature anomalies from NASA GISTEMP v4")
def global_anomalies(
    year: int = 0,
    session: Session = Depends(get_session),
):
    stmt = select(GlobalTemperatureAnomaly).order_by(
        GlobalTemperatureAnomaly.year.desc(),  # type: ignore[arg-type]
        GlobalTemperatureAnomaly.month.desc(),  # type: ignore[arg-type]
    )
    rows = session.exec(stmt).all()

    result = []
    for r in rows:
        if year and r.year != year:
            continue
        result.append({
            "year":             r.year,
            "month":            r.month,
            "month_name":       r.month_name,
            "anomaly_c":        r.anomaly_c,
            "source":           r.source,
            "baseline":         r.baseline_period,
            "all_time_rank":    r.all_time_rank,
            "is_record_warmest": r.is_record_warmest,
            "fetched_at":       r.fetched_at,
            "settlement_note":  "[NEEDS_CHECK] Exact Polymarket settlement source not verified",
        })

    return {
        "count": len(result),
        "source": "nasa_gistemp_v4",
        "baseline": "1951-1980",
        "settlement_warning": (
            "[NEEDS_CHECK] Polymarket 'hottest month on record' markets may use "
            "NOAA GlobalTemp or another dataset. Verify before using for signals."
        ),
        "anomalies": result,
    }


@router.post("/ingestion/run-once", summary="Run all weather ingestion sources once (local dev only)")
def run_weather_once():
    """
    Triggers one complete weather data fetch: NWS + Open-Meteo + NASA GISTEMP.
    Local development use only. No network write calls. Read-only.
    """
    from ingestion.nws import run_nws_ingestion
    from ingestion.openmeteo import run_openmeteo_ingestion
    from ingestion.noaa import run_noaa_ingestion

    results: dict = {}
    for name, fn in [("nws", run_nws_ingestion), ("openmeteo", run_openmeteo_ingestion), ("nasa_gistemp", run_noaa_ingestion)]:
        try:
            log = fn()
            results[name] = {
                "status": log.status,
                "records_stored": log.records_stored,
                "duration_ms": log.duration_ms,
                "error": log.error_message,
            }
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

    return results


@router.get("/ingestion/logs", summary="Recent weather ingestion log entries")
def weather_logs(limit: int = 20, session: Session = Depends(get_session)):
    logs = session.exec(
        select(WeatherIngestionLog).order_by(WeatherIngestionLog.id.desc()).limit(limit)  # type: ignore[arg-type]
    ).all()
    return {
        "count": len(logs),
        "logs": [
            {
                "run_at": l.run_at, "source": l.source, "status": l.status,
                "records_stored": l.records_stored, "stations_ok": l.stations_ok,
                "duration_ms": l.duration_ms, "error": l.error_message,
            }
            for l in logs
        ],
    }
