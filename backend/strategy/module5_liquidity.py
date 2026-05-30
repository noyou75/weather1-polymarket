"""
Module 5 — Liquidity / Spread / Staleness Filter.
Hard gate applied BEFORE any probability estimation.
If this module fails, no further analysis is done.

Rules (from Phase 0 / Section 7 risk rules):
- Skip if liquidity < $500
- Skip if spread > 5% of mid-price
- Skip if bestBid and bestAsk both missing
- Skip if market already resolved (end_date in past)
- Warn (but don't skip) if spread > 2%

v1.1 additions (Phase 6C):
- Skip if resolving within 24h (near-expiry — city markets distort signals on same/next day)
- WATCH_ONLY flag if resolving within 48h (no ENTER_CANDIDATE allowed)
"""
from dataclasses import dataclass
from datetime import datetime, timezone, date as date_type, timedelta


# Thresholds from Phase 0 plan
MIN_LIQUIDITY_USD   = 500.0
MAX_SPREAD_FRACTION = 0.05    # 5% of mid-price (Gamma API returns spread as fraction)
WARN_SPREAD         = 0.02    # 2% — note but don't skip

# v1.1 near-expiry thresholds
NEAR_EXPIRY_SKIP_HOURS  = 24   # skip if resolving within 24h
NEAR_EXPIRY_WATCH_HOURS = 48   # watch-only if resolving within 48h

REC_SKIP_LOW_LIQ     = "SKIP_LOW_LIQUIDITY"
REC_SKIP_WIDE_SPREAD  = "SKIP_WIDE_SPREAD"
REC_SKIP_STALE_DATA   = "SKIP_STALE_DATA"
REC_SKIP_RESOLVED     = "SKIP_ALREADY_RESOLVED"
REC_SKIP_NEAR_EXPIRY  = "SKIP_NEAR_EXPIRY"    # v1.1: resolving within 24h
REC_PASS             = "LIQUIDITY_PASS"


@dataclass
class LiquidityResult:
    passed: bool
    recommendation: str        # one of REC_* above if failed, REC_PASS if ok
    reason: str
    liquidity_usd: float | None
    spread_fraction: float | None
    spread_pct: str            # human-readable
    bid: float | None
    ask: float | None
    warn_wide_spread: bool
    near_expiry_watch_only: bool = False  # v1.1: True if within 48h — no ENTER allowed


def _today_utc() -> date_type:
    return datetime.now(timezone.utc).date()


def check(
    liquidity: float | None,
    spread: float | None,
    best_bid: float | None,
    best_ask: float | None,
    end_date: str | None,
    fetched_at: str | None,
) -> LiquidityResult:
    """
    Apply all Module 5 hard-gate checks.
    Returns a LiquidityResult — if .passed is False, skip this market entirely.
    """
    spread_pct = f"{spread * 100:.1f}%" if spread is not None else "unknown"
    near_expiry_watch_only = False

    # 1. Market already resolved or near-expiry check
    if end_date:
        try:
            resolution_date = date_type.fromisoformat(end_date[:10])
            today = _today_utc()

            if resolution_date < today:
                return LiquidityResult(
                    passed=False,
                    recommendation=REC_SKIP_RESOLVED,
                    reason=f"Market resolution date {end_date[:10]} is in the past",
                    liquidity_usd=liquidity, spread_fraction=spread, spread_pct=spread_pct,
                    bid=best_bid, ask=best_ask, warn_wide_spread=False,
                )

            # v1.1: skip if resolving within 24h (same-day/next-day markets)
            days_to_resolution = (resolution_date - today).days
            if days_to_resolution < 1:
                return LiquidityResult(
                    passed=False,
                    recommendation=REC_SKIP_NEAR_EXPIRY,
                    reason=f"v1.1: Market resolves within 24h ({end_date[:10]}) — near-expiry signals disabled",
                    liquidity_usd=liquidity, spread_fraction=spread, spread_pct=spread_pct,
                    bid=best_bid, ask=best_ask, warn_wide_spread=False,
                )

            # v1.1: flag watch-only if resolving within 48h
            if days_to_resolution < 2:
                near_expiry_watch_only = True

        except ValueError:
            pass

    # 2. Missing price data?
    if best_bid is None and best_ask is None:
        return LiquidityResult(
            passed=False,
            recommendation=REC_SKIP_STALE_DATA,
            reason="No bid/ask price data available",
            liquidity_usd=liquidity, spread_fraction=spread, spread_pct=spread_pct,
            bid=None, ask=None, warn_wide_spread=False,
        )

    # 3. Insufficient liquidity?
    if liquidity is None or liquidity < MIN_LIQUIDITY_USD:
        return LiquidityResult(
            passed=False,
            recommendation=REC_SKIP_LOW_LIQ,
            reason=f"Liquidity ${liquidity or 0:,.0f} < ${MIN_LIQUIDITY_USD:,.0f} threshold",
            liquidity_usd=liquidity, spread_fraction=spread, spread_pct=spread_pct,
            bid=best_bid, ask=best_ask, warn_wide_spread=False,
        )

    # 4. Spread too wide?
    if spread is not None and spread > MAX_SPREAD_FRACTION:
        return LiquidityResult(
            passed=False,
            recommendation=REC_SKIP_WIDE_SPREAD,
            reason=f"Spread {spread_pct} > {MAX_SPREAD_FRACTION*100:.0f}% threshold",
            liquidity_usd=liquidity, spread_fraction=spread, spread_pct=spread_pct,
            bid=best_bid, ask=best_ask, warn_wide_spread=True,
        )

    # Pass — compute implied probability from mid-price
    warn = (spread or 0) > WARN_SPREAD

    near_expiry_note = " (48h watch-only — no ENTER_CANDIDATE)" if near_expiry_watch_only else ""
    return LiquidityResult(
        passed=True,
        recommendation=REC_PASS,
        reason=f"Passed all liquidity checks{near_expiry_note}",
        liquidity_usd=liquidity, spread_fraction=spread, spread_pct=spread_pct,
        bid=best_bid, ask=best_ask, warn_wide_spread=warn,
        near_expiry_watch_only=near_expiry_watch_only,
    )


def implied_probability(best_bid: float | None, best_ask: float | None) -> float | None:
    """Mid-price as implied YES probability. Returns None if prices missing."""
    if best_bid is None and best_ask is None:
        return None
    if best_bid is None:
        return best_ask
    if best_ask is None:
        return best_bid
    return round((best_bid + best_ask) / 2, 4)
