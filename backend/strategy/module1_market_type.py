"""
Module 1 — Market Type Classifier.
Classifies Polymarket weather markets into analytical categories.

v1.1 changes (Phase 6C):
- TYPE_ANNUAL_TEMP now only covers rank-1 ("hottest year ever") markets.
- TYPE_ANNUAL_RANK_LOWER added for rank-2+ markets → DISABLED (0% win rate in v1.0).
- SUPPORTED_TYPES updated to exclude annual_rank_lower.
"""
import re
from dataclasses import dataclass


# ── Market type constants ─────────────────────────────────────────────────────
TYPE_ANNUAL_TEMP         = "annual_temp"           # RANK-1 ONLY: "Will 2026 be the hottest year?"
TYPE_ANNUAL_RANK_LOWER   = "annual_rank_lower"     # DISABLED: rank-2/3/4/5/6 ("second-hottest", etc.)
TYPE_GLOBAL_MONTHLY_TEMP = "global_monthly_temp"   # "Will global temp increase by X in May?"
TYPE_CITY_STATION_TEMP   = "city_station_temp"     # "Will highest temp in NYC be X°F on date?"
TYPE_HURRICANE           = "hurricane"
TYPE_TORNADO             = "tornado"
TYPE_EARTHQUAKE          = "earthquake"
TYPE_VOLCANO             = "volcano"
TYPE_ARCTIC_ICE          = "arctic_ice"
TYPE_PRECIPITATION       = "precipitation"
TYPE_DISEASE             = "disease"
TYPE_EXCLUDED            = "excluded"

# v1.1: rank-2+ keywords — must be checked BEFORE rank-1 keywords
_RANK_LOWER_KWS = [
    "second-hottest", "second hottest",
    "third-hottest",  "third hottest",
    "fourth-hottest", "fourth hottest",
    "fifth-hottest",  "fifth hottest",
    "sixth-hottest",  "sixth hottest",
    "sixth or lower", "sixth-or-lower",
    "rank as the second", "rank as the third",
    "rank as the fourth", "rank as the fifth",
    "rank as the sixth",
]

# Cities with NWS/Open-Meteo data in Phase 4
SUPPORTED_CITIES: dict[str, str] = {
    "new york city": "NYC_LGA",
    "new york":      "NYC_LGA",
    "nyc":           "NYC_LGA",
    "dallas":        "DAL_DAL",
    "miami":         "MIA_MIA",
    "phoenix":       "PHX_SKY",
    "chicago":       "CHI_ORD",
    "los angeles":   "LAX_LAX",
    "la":            "LAX_LAX",
}

# v1.1 supported types (signal generation attempted)
# NOTE: TYPE_ANNUAL_RANK_LOWER is deliberately excluded — 0% win rate, disabled.
SUPPORTED_TYPES = {TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP, TYPE_CITY_STATION_TEMP}


@dataclass
class ClassificationResult:
    market_type: str
    station_id: str | None        # for city_station_temp
    city_name: str | None         # human-readable city
    temp_range_low_f: float | None   # lower temp threshold (°F)
    temp_range_high_f: float | None  # upper temp threshold (°F)
    temp_range_low_c: float | None   # lower temp threshold (°C) for anomaly markets
    temp_range_high_c: float | None  # upper temp threshold (°C) for anomaly markets
    target_date: str | None          # YYYY-MM-DD for city/monthly markets
    skip_reason: str | None          # if not supported


def _f_to_c(f: float) -> float:
    return round((f - 32) * 5 / 9, 2)


def classify_market(question: str, event_title: str, end_date: str | None) -> ClassificationResult:
    """Classify a market by its question text and event title."""
    q = (question or "").lower().strip()
    et = (event_title or "").lower().strip()

    # ── Annual temperature rank-2+ (DISABLED in v1.1) — must check BEFORE rank-1 ──
    if any(kw in q for kw in _RANK_LOWER_KWS):
        return ClassificationResult(
            market_type=TYPE_ANNUAL_RANK_LOWER,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None,
            skip_reason=(
                "v1.1: Rank-2+ annual temperature markets are DISABLED. "
                "Phase 6B diagnosis: 0% win rate (14/14 losses). "
                "Structural logic flaw — cannot be fixed by calibration."
            ),
        )

    # ── Annual temperature rank-1 only ("hottest year on record") ─────────────
    if any(kw in q for kw in ["hottest year on record", "warmest year on record",
                                "rank as the", "rank among the hottest"]):
        return ClassificationResult(
            market_type=TYPE_ANNUAL_TEMP,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason=None,
        )

    # ── Global monthly temperature anomaly ───────────────────────────────────
    # "Will global temperature increase by between 1.10ºC and 1.14ºC in May 2026?"
    if ("global temperature" in q and ("increase" in q or "anomaly" in q)) or \
       ("temperature increase" in q and ("ºc" in q or "°c" in q or "c in " in q)):
        # Parse °C thresholds from question
        bounds = re.findall(r'(\d+\.\d+)', q)
        low_c = float(bounds[0]) if len(bounds) >= 1 else None
        high_c = float(bounds[1]) if len(bounds) >= 2 else None
        # "less than X" → low=0, high=X
        if "less than" in q and low_c is not None:
            high_c = low_c; low_c = 0.0
        # "more than X" → low=X, high=999
        if "more than" in q and low_c is not None:
            high_c = 999.0
        return ClassificationResult(
            market_type=TYPE_GLOBAL_MONTHLY_TEMP,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=low_c, temp_range_high_c=high_c,
            target_date=end_date[:10] if end_date else None,
            skip_reason=None,
        )

    # ── City / station temperature ────────────────────────────────────────────
    # "Will the highest temperature in New York City be between 78-79°F on May 30?"
    if "highest temperature in" in q and "°f" in q:
        # Extract city name
        city_match = re.search(r'highest temperature in (.+?) be', q)
        city_raw = city_match.group(1).strip() if city_match else ""
        station_id = None
        matched_city = None
        for city_key, sid in SUPPORTED_CITIES.items():
            if city_key in city_raw:
                station_id = sid
                matched_city = city_key
                break

        # Parse temperature range in °F
        # "between X-Y°F" or "X°F or below" or "X°F or above" or "more than X°F"
        range_match = re.search(r'between (\d+)[–\-](\d+).*?°f', q)
        below_match = re.search(r'(\d+).*?°f or below', q)
        above_match = re.search(r'more than (\d+).*?°f|(\d+).*?°f or above', q)

        low_f = high_f = None
        if range_match:
            low_f = float(range_match.group(1))
            high_f = float(range_match.group(2))
        elif below_match:
            low_f = -999.0
            high_f = float(below_match.group(1))
        elif above_match:
            val = above_match.group(1) or above_match.group(2)
            if val:
                low_f = float(val)
                high_f = 999.0

        return ClassificationResult(
            market_type=TYPE_CITY_STATION_TEMP,
            station_id=station_id,
            city_name=matched_city,
            temp_range_low_f=low_f, temp_range_high_f=high_f,
            temp_range_low_c=_f_to_c(low_f) if low_f and low_f > -999 else None,
            temp_range_high_c=_f_to_c(high_f) if high_f and high_f < 999 else None,
            target_date=end_date[:10] if end_date else None,
            skip_reason=None if station_id else f"City '{city_raw}' not in NWS seed list",
        )

    # ── Precipitation ─────────────────────────────────────────────────────────
    if "precipitation" in q or "rainfall" in q or "snowfall" in q:
        return ClassificationResult(
            market_type=TYPE_PRECIPITATION,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason="Precipitation markets not supported in Phase 5",
        )

    # ── Hurricane / tropical ──────────────────────────────────────────────────
    if any(kw in q or kw in et for kw in ["hurricane", "tropical storm", "cyclone", "typhoon", "landfall", "named storm"]):
        return ClassificationResult(
            market_type=TYPE_HURRICANE,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason="Hurricane markets not supported in Phase 5",
        )

    # ── Tornado ───────────────────────────────────────────────────────────────
    if "tornado" in q or "tornado" in et:
        return ClassificationResult(
            market_type=TYPE_TORNADO,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason="Tornado markets not supported in Phase 5",
        )

    # ── Earthquake / volcano ──────────────────────────────────────────────────
    if any(kw in q for kw in ["earthquake", "megaquake", "seismic", "volcano", "eruption", "vei"]):
        return ClassificationResult(
            market_type=TYPE_EARTHQUAKE,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason="Geological event markets not supported in Phase 5",
        )

    # ── Arctic / ice ──────────────────────────────────────────────────────────
    if any(kw in q or kw in et for kw in ["arctic", "sea ice", "glacier", "ice extent"]):
        return ClassificationResult(
            market_type=TYPE_ARCTIC_ICE,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason="Arctic/ice markets not supported in Phase 5",
        )

    # ── Disease / other ───────────────────────────────────────────────────────
    if any(kw in q for kw in ["measles", "ebola", "cases", "disease", "outbreak", "flu"]):
        return ClassificationResult(
            market_type=TYPE_DISEASE,
            station_id=None, city_name=None,
            temp_range_low_f=None, temp_range_high_f=None,
            temp_range_low_c=None, temp_range_high_c=None,
            target_date=None, skip_reason="Disease/health markets not weather temperature markets",
        )

    # ── Fallback ──────────────────────────────────────────────────────────────
    return ClassificationResult(
        market_type=TYPE_EXCLUDED,
        station_id=None, city_name=None,
        temp_range_low_f=None, temp_range_high_f=None,
        temp_range_low_c=None, temp_range_high_c=None,
        target_date=None, skip_reason=f"Market type not classified (question: {question[:60]})",
    )
