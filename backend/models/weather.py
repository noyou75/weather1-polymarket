"""
Weather data models — Phase 4.
All data is read-only from public APIs. No authentication. No private keys.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class WeatherStation(SQLModel, table=True):
    """Seed list of US city stations relevant to Polymarket weather markets."""
    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: str = Field(index=True, unique=True)  # e.g. "NYC_LGA"
    name: str                                           # human-readable name
    city: str
    state: Optional[str] = None
    country: str = "US"
    latitude: float
    longitude: float
    nws_grid_id: Optional[str] = None      # NWS grid office (e.g. "OKX")
    nws_grid_x: Optional[int] = None
    nws_grid_y: Optional[int] = None
    nws_forecast_url: Optional[str] = None  # cached forecast URL from /points
    timezone: str = "America/New_York"
    notes: Optional[str] = None             # why this city is in the seed list


class WeatherForecast(SQLModel, table=True):
    """
    Daily temperature forecast per station, per source.
    Stores max/min temps for upcoming days — used by Module 2 (forecast vs market gap).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: str = Field(index=True)
    source: str                              # "nws" | "openmeteo"
    forecast_date: str                       # YYYY-MM-DD (the day being forecast)
    period_label: Optional[str] = None       # NWS period name, e.g. "Today", "Saturday"
    temperature_max_f: Optional[float] = None
    temperature_min_f: Optional[float] = None
    temperature_max_c: Optional[float] = None
    temperature_min_c: Optional[float] = None
    precipitation_mm: Optional[float] = None
    wind_speed_text: Optional[str] = None    # NWS: "18 to 23 mph"
    short_forecast: Optional[str] = None     # NWS: "Partly Sunny"
    prob_precipitation: Optional[float] = None  # 0–100 %
    fetched_at: str = ""                     # ISO UTC timestamp of this fetch
    valid_from: Optional[str] = None         # ISO period start time


class GlobalTemperatureAnomaly(SQLModel, table=True):
    """
    Monthly global surface temperature anomaly from NASA GISTEMP v4.
    Baseline: 1951–1980 average.

    SETTLEMENT NOTE [NEEDS_CHECK]: Polymarket 'hottest month on record' markets
    may use NOAA GlobalTemp or NASA GISTEMP as the settlement source.
    This data uses NASA GISTEMP v4 (GLB.Ts+dSST.csv). Verify exact
    settlement source before using for signal generation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    month: int = Field(index=True)            # 1–12
    month_name: str = ""                      # "Jan", "Feb", etc.
    anomaly_c: Optional[float] = None         # °C above 1951–1980 baseline
    source: str = "nasa_gistemp_v4"
    baseline_period: str = "1951-1980"
    is_record_warmest: Optional[bool] = None  # computed after full record loaded
    all_time_rank: Optional[int] = None       # rank among all same months (1 = warmest)
    fetched_at: str = ""

    # Settlement alignment
    settlement_note: str = (
        "[NEEDS_CHECK] Settlement source not verified for Polymarket markets. "
        "This is NASA GISTEMP v4 data. Polymarket may use NOAA GlobalTemp."
    )


class WeatherIngestionLog(SQLModel, table=True):
    """Log of each weather data fetch attempt."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_at: str = ""
    source: str = ""          # "nws" | "openmeteo" | "nasa_gistemp"
    status: str = ""          # "ok" | "partial" | "error"
    stations_attempted: int = 0
    stations_ok: int = 0
    records_stored: int = 0
    duration_ms: int = 0
    error_message: Optional[str] = None
