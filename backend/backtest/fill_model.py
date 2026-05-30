"""
Fill model — Phase 6.
Simulates entry/exit fills for backtesting with conservative slippage assumptions.

IMPORTANT: No historical Polymarket price data is available.
Entry prices are ESTIMATED conservatively based on:
  - Signal direction and confidence
  - Known final resolution outcome
This makes P&L estimates rough. Quality rating: LOW for P&L, MEDIUM for directional accuracy.

Slippage from Phase 0 Section 8:
  Entry:            1.0% of mid-price
  Exit:             0.5% of mid-price
  Near-resolution:  1.5% additional (within 48h of settlement)
"""
from dataclasses import dataclass


# Slippage constants from Phase 0 plan
ENTRY_SLIPPAGE_PCT     = 0.01   # 1% on entry
EXIT_SLIPPAGE_PCT      = 0.005  # 0.5% on exit
NEAR_RES_SLIPPAGE_PCT  = 0.015  # 1.5% additional near resolution

# Conservative price estimate buckets (no actual historical prices)
# When signal says YES and gap is large, market was likely underpricing YES
# We use conservative middle-ground estimates to avoid overestimating P&L
ESTIMATED_PRICE_STRONG_YES   = 0.45  # market was underpricing, we buy YES cheaply
ESTIMATED_PRICE_MODERATE_YES = 0.50  # moderate gap
ESTIMATED_PRICE_STRONG_NO    = 0.55  # YES was overpriced, we buy NO at low price
ESTIMATED_PRICE_MODERATE_NO  = 0.50

# Note: binary prediction markets settle at 1.0 (YES wins) or 0.0 (NO wins)
RESOLUTION_YES = 1.0
RESOLUTION_NO  = 0.0


@dataclass
class FillResult:
    entry_price_estimated: float    # before slippage
    entry_price_filled: float       # after entry slippage
    exit_price_estimated: float     # resolution outcome
    exit_price_filled: float        # after exit slippage
    entry_slippage_pct: float
    exit_slippage_pct: float
    is_near_resolution: bool
    price_quality: str              # "estimated" always in Phase 6


def estimate_entry_price(signal_side: str, gap_pp: float | None, confidence: int) -> float:
    """
    Estimate the entry price based on signal characteristics.
    Conservative: assumes market had already partially priced in our signal.
    """
    if signal_side == "YES":
        if gap_pp is not None and abs(gap_pp) >= 15:
            return ESTIMATED_PRICE_STRONG_YES
        return ESTIMATED_PRICE_MODERATE_YES
    elif signal_side == "NO":
        if gap_pp is not None and abs(gap_pp) >= 15:
            return 1.0 - ESTIMATED_PRICE_STRONG_NO   # buying NO = 1 - price
        return 1.0 - ESTIMATED_PRICE_MODERATE_NO
    return 0.50  # WATCH → no directional entry


def simulate_fill(
    signal_side: str,
    gap_pp: float | None,
    confidence: int,
    resolved_yes: bool,
    is_near_resolution: bool = False,
) -> FillResult:
    """
    Simulate one round-trip fill.
    Entry: estimated price + slippage.
    Exit: resolution outcome (1.0 or 0.0) - slippage.
    """
    entry_est = estimate_entry_price(signal_side, gap_pp, confidence)

    # Entry slippage: always buy at ask (worse price for us)
    entry_slip = ENTRY_SLIPPAGE_PCT
    if signal_side == "YES":
        entry_filled = min(entry_est * (1 + entry_slip), 0.99)
    else:  # NO — we pay 1-price for the NO token
        no_price_est = 1.0 - entry_est
        entry_filled = min(no_price_est * (1 + entry_slip), 0.99)
        entry_est = no_price_est  # store as NO token cost

    # Exit: resolution value
    resolution = RESOLUTION_YES if resolved_yes else RESOLUTION_NO
    exit_slip = EXIT_SLIPPAGE_PCT
    if is_near_resolution:
        exit_slip += NEAR_RES_SLIPPAGE_PCT

    # For the EXIT: if holding YES token, resolution=1.0 → sell near 1.0
    # If holding NO token, resolution=0.0 for YES → NO token = 1.0
    if signal_side == "YES":
        exit_est = resolution
        exit_filled = max(exit_est * (1 - exit_slip), 0.0)
    else:
        no_resolution = 1.0 - resolution   # NO token value
        exit_est = no_resolution
        exit_filled = max(exit_est * (1 - exit_slip), 0.0)

    return FillResult(
        entry_price_estimated=round(entry_est, 4),
        entry_price_filled=round(entry_filled, 4),
        exit_price_estimated=round(exit_est, 4),
        exit_price_filled=round(exit_filled, 4),
        entry_slippage_pct=round(entry_slip * 100, 2),
        exit_slippage_pct=round(exit_slip * 100, 2),
        is_near_resolution=is_near_resolution,
        price_quality="estimated",
    )


def compute_pnl(fill: FillResult, size_usd: float) -> tuple[float, float]:
    """
    Compute (pnl_usd, pnl_pct) from fill result.
    P&L = (exit_filled - entry_filled) / entry_filled * size_usd
    """
    if fill.entry_price_filled <= 0:
        return 0.0, 0.0
    pnl_pct = (fill.exit_price_filled - fill.entry_price_filled) / fill.entry_price_filled
    pnl_usd = size_usd * pnl_pct
    return round(pnl_usd, 4), round(pnl_pct * 100, 4)
