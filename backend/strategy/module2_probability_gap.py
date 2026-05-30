"""
Module 2 — Forecast vs Market Probability Gap.
Estimates true probability from available weather data and compares to market implied probability.

Phase 6D UPDATE — Settlement source VERIFIED:
  All annual and monthly global temperature markets use the "Global Land-Ocean Temperature Index"
  (NASA GISTEMP v4) as their official resolution source, confirmed from closed market descriptions.
  Source: https://data.giss.nasa.gov/gistemp/
  Evidence: 11 closed events (Apr 2024 – Mar 2025) all cite identical boilerplate.

  For annual_temp and global_monthly_temp markets: settlement_verified = True.
  For city_station_temp and others: settlement_verified = False (NWS ≠ Polymarket source).

REMAINING CAVEATS:
- Probability estimates are analytical estimates, not precise forecasts.
- A gap > 10pp is a signal for further analysis, not guaranteed edge.
- Entry prices in backtesting remain estimated (no historical trade prices available).
"""
import re
import logging
from dataclasses import dataclass
from datetime import date as date_type, datetime, timezone

from sqlmodel import Session, select

from database import engine
from models.weather import GlobalTemperatureAnomaly, WeatherForecast, WeatherStation
from strategy.module1_market_type import ClassificationResult, SUPPORTED_CITIES

logger = logging.getLogger("weather1.strategy.module2")

# Phase 6D: settlement source CONFIRMED for annual_temp and global_monthly_temp
SETTLEMENT_NOTE_VERIFIED = (
    "[VERIFIED] Settlement source confirmed: Global Land-Ocean Temperature Index "
    "(NASA GISTEMP v4). Verified from 11 closed Polymarket market descriptions (Phase 6D)."
)
SETTLEMENT_NOTE_UNVERIFIED = (
    "[NEEDS_CHECK] Settlement source not confirmed for this market type. "
    "Do not use for trading without independent verification."
)
# Legacy alias
SETTLEMENT_NOTE = SETTLEMENT_NOTE_VERIFIED  # default for annual_temp/global_monthly_temp


@dataclass
class ProbabilityResult:
    estimated_prob: float | None   # 0.0–1.0 model estimate
    gap_pp: float | None           # (estimated - market_implied) * 100, positive = model higher
    data_quality: str              # "good" | "partial" | "insufficient"
    settlement_verified: bool      # always False in Phase 5 (NEEDS_CHECK)
    explanation: str
    data_source: str               # which data was used
    confidence_contribution: int   # 0-45 points toward total confidence


def _no_data(reason: str) -> ProbabilityResult:
    return ProbabilityResult(
        estimated_prob=None, gap_pp=None, data_quality="insufficient",
        settlement_verified=False, explanation=reason,
        data_source="none", confidence_contribution=0,
    )


# ── Annual temperature rank ───────────────────────────────────────────────────
def estimate_annual_temp(question: str, market_implied_prob: float | None) -> ProbabilityResult:
    """
    Estimate probability for 'Will 2026 be the Nth hottest year on record?'
    Uses NASA GISTEMP partial year data (Jan–Apr 2026) to assess 2026 trajectory.
    """
    with Session(engine) as s:
        anomalies = s.exec(select(GlobalTemperatureAnomaly)).all()

    if not anomalies:
        return _no_data("No GISTEMP anomaly data in database. Run POST /weather/ingestion/run-once first.")

    # Compute annual averages from stored data
    by_year: dict[int, list[float]] = {}
    for a in anomalies:
        if a.anomaly_c is not None:
            by_year.setdefault(a.year, []).append(a.anomaly_c)

    # Only count years with ≥10 months for a reliable annual average
    full_year_avgs = {yr: sum(v) / len(v) for yr, v in by_year.items() if len(v) >= 10}
    partial_2026 = by_year.get(2026, [])

    if not partial_2026:
        return _no_data("No 2026 GISTEMP data available yet.")

    avg_2026_partial = sum(partial_2026) / len(partial_2026)
    months_available = len(partial_2026)

    # Best prior year record from our dataset
    if full_year_avgs:
        best_prior_yr = max(full_year_avgs, key=full_year_avgs.get)
        best_prior_avg = full_year_avgs[best_prior_yr]
    else:
        # Approximate from historical knowledge if dataset too short
        best_prior_yr, best_prior_avg = 2024, 1.29

    # Parse which rank this market is asking about
    q_lower = question.lower()
    is_hottest  = "hottest year on record" in q_lower and "second" not in q_lower and "third" not in q_lower
    is_second   = "second-hottest" in q_lower or "second hottest" in q_lower
    is_third    = "third-hottest" in q_lower or "third hottest" in q_lower
    is_fourth   = "fourth-hottest" in q_lower
    is_fifth    = "fifth-hottest" in q_lower
    is_sixth    = "sixth-hottest" in q_lower or "sixth or lower" in q_lower

    pace_vs_record = avg_2026_partial - best_prior_avg
    pace_desc = f"+{pace_vs_record:.3f}°C vs prior record" if pace_vs_record >= 0 else f"{pace_vs_record:.3f}°C vs prior record"

    # Conservative probability estimate based on trajectory
    # If 2026 partial avg > prior record → high chance of #1
    # We use a simple heuristic, not a statistical model
    if is_hottest:
        if avg_2026_partial > best_prior_avg + 0.05:
            est_prob = 0.70
        elif avg_2026_partial > best_prior_avg - 0.05:
            est_prob = 0.50
        elif avg_2026_partial > best_prior_avg - 0.15:
            est_prob = 0.35
        else:
            est_prob = 0.20
    elif is_second:
        # Complementary — if not #1, likely #2
        hottest_prob = 0.40 if avg_2026_partial > best_prior_avg - 0.15 else 0.25
        est_prob = min(0.75, (1 - hottest_prob) * 0.7)
    elif is_third:
        est_prob = 0.15
    elif is_fourth:
        est_prob = 0.05
    elif is_fifth:
        est_prob = 0.03
    elif is_sixth:
        est_prob = 0.02
    else:
        return _no_data(f"Could not determine rank from question: {question[:80]}")

    gap_pp = ((est_prob - market_implied_prob) * 100) if market_implied_prob is not None else None

    conf = 0
    if gap_pp is not None:
        abs_gap = abs(gap_pp)
        if abs_gap >= 15:
            conf = 35
        elif abs_gap >= 8:
            conf = 25
        elif abs_gap >= 4:
            conf = 15
        else:
            conf = 5
    # Cap at 45 because settlement is unverified
    conf = min(conf, 40)

    explanation = (
        f"2026 partial avg ({months_available} months): +{avg_2026_partial:.2f}°C. "
        f"Best prior record: {best_prior_yr} at +{best_prior_avg:.2f}°C ({pace_desc}). "
        f"Estimated YES prob: {est_prob:.0%}. "
        f"Market implied: {market_implied_prob:.0%}. "
        f"Gap: {gap_pp:+.1f}pp. "
        f"{SETTLEMENT_NOTE_VERIFIED}"
    )

    return ProbabilityResult(
        estimated_prob=round(est_prob, 4),
        gap_pp=round(gap_pp, 2) if gap_pp is not None else None,
        data_quality="partial",
        settlement_verified=True,   # Phase 6D: CONFIRMED = NASA GISTEMP
        explanation=explanation,
        data_source=f"nasa_gistemp_v4 ({months_available} months of 2026)",
        confidence_contribution=conf,
    )


# ── Global monthly temperature anomaly ───────────────────────────────────────
def estimate_global_monthly(
    question: str,
    cl: ClassificationResult,
    market_implied_prob: float | None,
) -> ProbabilityResult:
    """
    Estimate probability for 'Will global temp increase by X-Y°C in [Month]?'
    Uses GISTEMP recent trend as context. Cannot directly predict future months.
    May 2026 data not yet published (released ~4 weeks after month end).
    """
    with Session(engine) as s:
        recent = s.exec(
            select(GlobalTemperatureAnomaly)
            .order_by(GlobalTemperatureAnomaly.year.desc(),   # type: ignore[arg-type]
                      GlobalTemperatureAnomaly.month.desc())  # type: ignore[arg-type]
            .limit(6)
        ).all()

    if not recent:
        return _no_data("No GISTEMP data available for monthly trend estimation.")

    # Most recent available months
    avg_recent = sum(a.anomaly_c for a in recent if a.anomaly_c) / len(recent)
    latest = recent[0]

    low_c = cl.temp_range_low_c
    high_c = cl.temp_range_high_c

    if low_c is None:
        return _no_data("Could not parse temperature range from market question.")

    # Does the recent trend suggest this range is likely?
    # This is a rough heuristic — not a model
    in_range = False
    if low_c == 0 and high_c is not None:
        in_range = avg_recent < high_c   # "less than X"
    elif high_c == 999:
        in_range = avg_recent > low_c     # "more than X"
    elif high_c is not None:
        in_range = low_c - 0.10 <= avg_recent <= high_c + 0.10

    est_prob = 0.65 if in_range else 0.25
    gap_pp = ((est_prob - market_implied_prob) * 100) if market_implied_prob is not None else None

    conf = 10 if gap_pp is not None and abs(gap_pp) >= 5 else 5
    # Low confidence — monthly data not published, extrapolating from trend
    conf = min(conf, 15)

    explanation = (
        f"Recent GISTEMP avg (last {len(recent)} months): +{avg_recent:.2f}°C. "
        f"Latest: {latest.year}-{latest.month_name} at +{latest.anomaly_c}°C. "
        f"Target range: {low_c}–{high_c}°C. "
        f"Trend {'inside' if in_range else 'outside'} range. "
        f"Note: {question[:30][:100]} data NOT YET PUBLISHED — this is trend extrapolation only. "
        f"{SETTLEMENT_NOTE_VERIFIED}"
    )

    return ProbabilityResult(
        estimated_prob=round(est_prob, 4),
        gap_pp=round(gap_pp, 2) if gap_pp is not None else None,
        data_quality="partial",
        settlement_verified=True,   # Phase 6D: CONFIRMED = NASA GISTEMP
        explanation=explanation,
        data_source=f"nasa_gistemp_v4 trend (latest: {latest.year}-{latest.month_name})",
        confidence_contribution=conf,
    )


# ── City / station temperature ────────────────────────────────────────────────
def estimate_city_temp(
    cl: ClassificationResult,
    market_implied_prob: float | None,
) -> ProbabilityResult:
    """
    Estimate probability for city temp markets using NWS + Open-Meteo forecasts.
    Only reliable within the 7-day forecast window.
    """
    if not cl.station_id:
        return _no_data(f"City not in NWS seed list: {cl.city_name}")

    if not cl.target_date:
        return _no_data("Could not extract target date from market.")

    try:
        target = date_type.fromisoformat(cl.target_date)
        today = datetime.now(timezone.utc).date()
        days_out = (target - today).days
        if days_out < 0:
            return _no_data(f"Target date {cl.target_date} is in the past.")
        if days_out > 7:
            return _no_data(f"Target date {cl.target_date} is {days_out} days out — beyond 7-day forecast window.")
    except ValueError:
        return _no_data(f"Could not parse target date: {cl.target_date}")

    if cl.temp_range_low_f is None or cl.temp_range_high_f is None:
        return _no_data("Could not parse temperature range from question.")

    with Session(engine) as s:
        # Get latest NWS forecast for this station and date
        nws_rows = s.exec(
            select(WeatherForecast).where(
                WeatherForecast.station_id == cl.station_id,
                WeatherForecast.source == "nws",
                WeatherForecast.forecast_date == cl.target_date,
            ).order_by(WeatherForecast.id.desc())  # type: ignore[arg-type]
            .limit(5)
        ).all()
        # Open-Meteo forecast
        om_rows = s.exec(
            select(WeatherForecast).where(
                WeatherForecast.station_id == cl.station_id,
                WeatherForecast.source == "openmeteo",
                WeatherForecast.forecast_date == cl.target_date,
            ).order_by(WeatherForecast.id.desc())  # type: ignore[arg-type]
            .limit(1)
        ).all()

    # Get daytime high from NWS
    nws_high_f: float | None = None
    for row in nws_rows:
        if row.temperature_max_f is not None:
            nws_high_f = row.temperature_max_f
            break

    # Open-Meteo max
    om_high_f: float | None = None
    if om_rows and om_rows[0].temperature_max_f is not None:
        om_high_f = om_rows[0].temperature_max_f

    if nws_high_f is None and om_high_f is None:
        return _no_data(f"No forecast data for {cl.station_id} on {cl.target_date}.")

    # Use NWS as primary, OM as fallback/confirmation
    primary_high = nws_high_f or om_high_f
    sources_agree = (nws_high_f is not None and om_high_f is not None and
                     abs(nws_high_f - om_high_f) <= 5)

    low_f = cl.temp_range_low_f
    high_f = cl.temp_range_high_f
    in_range = (low_f <= primary_high <= high_f) if primary_high else False

    # Probability estimate:
    # If forecast squarely in range → high YES probability
    # If forecast at edge of range → moderate
    # If forecast outside range → low YES probability
    if primary_high is not None and high_f < 999 and low_f > -999:
        range_center = (low_f + high_f) / 2
        range_half = (high_f - low_f) / 2 + 3.0   # +3°F buffer for forecast uncertainty
        dist_from_center = abs(primary_high - range_center)

        if dist_from_center <= range_half * 0.5:    # clearly in range
            est_prob = 0.75 if sources_agree else 0.65
        elif dist_from_center <= range_half * 1.0:  # at edge
            est_prob = 0.55 if in_range else 0.35
        else:                                         # outside range
            est_prob = 0.20 if in_range else 0.10
    elif high_f >= 999:    # "above X°F"
        est_prob = 0.70 if (primary_high or 0) > low_f else 0.25
    elif low_f <= -999:    # "below X°F"
        est_prob = 0.70 if (primary_high or 0) < high_f else 0.25
    else:
        est_prob = 0.50

    gap_pp = ((est_prob - market_implied_prob) * 100) if market_implied_prob is not None else None

    # Confidence based on: gap size, days_out, source agreement
    conf = 0
    if gap_pp is not None:
        if abs(gap_pp) >= 15:
            conf = 40
        elif abs(gap_pp) >= 8:
            conf = 28
        elif abs(gap_pp) >= 4:
            conf = 15
        else:
            conf = 8
    # Penalty for forecast uncertainty by day
    day_penalty = days_out * 4   # -4 points per day out
    conf = max(0, conf - day_penalty)
    if sources_agree:
        conf = min(45, conf + 8)

    src_parts = []
    if nws_high_f is not None:
        src_parts.append(f"NWS={nws_high_f}°F")
    if om_high_f is not None:
        src_parts.append(f"OM={om_high_f}°F")
    src_str = ", ".join(src_parts)

    explanation = (
        f"Forecast high for {cl.city_name} on {cl.target_date}: {src_str}. "
        f"Market range: {low_f}–{high_f}°F. "
        f"Forecast {'IN' if in_range else 'OUT OF'} range. "
        f"{'Sources agree (±5°F).' if sources_agree else 'Sources disagree or single source.'} "
        f"Days out: {days_out}. Confidence penalty: -{day_penalty}pts. "
        f"Note: NWS/Open-Meteo are the data sources; these are NOT official settlement sources for Polymarket."
    )

    return ProbabilityResult(
        estimated_prob=round(est_prob, 4),
        gap_pp=round(gap_pp, 2) if gap_pp is not None else None,
        data_quality="good" if sources_agree else "partial",
        settlement_verified=False,
        explanation=explanation,
        data_source=f"nws+openmeteo ({src_str})",
        confidence_contribution=conf,
    )


def estimate(
    market_type: str,
    question: str,
    cl: ClassificationResult,
    market_implied_prob: float | None,
) -> ProbabilityResult:
    """Dispatch to the right estimation function based on market type."""
    from strategy.module1_market_type import (
        TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP, TYPE_CITY_STATION_TEMP
    )

    if market_type == TYPE_ANNUAL_TEMP:
        return estimate_annual_temp(question, market_implied_prob)
    elif market_type == TYPE_GLOBAL_MONTHLY_TEMP:
        return estimate_global_monthly(question, cl, market_implied_prob)
    elif market_type == TYPE_CITY_STATION_TEMP:
        return estimate_city_temp(cl, market_implied_prob)
    else:
        return _no_data(f"Market type '{market_type}' not supported by Module 2")
