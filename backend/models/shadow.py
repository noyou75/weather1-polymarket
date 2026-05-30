"""
Shadow signal observation models — Phase 6E.

IMPORTANT: These models record OBSERVATION DATA ONLY.
- No positions are created.
- No capital is debited.
- No portfolio P&L is tracked.
- No paper trades are executed.
- "directional_move_pct" is market movement after signal — NOT portfolio return.

Purpose: Collect real live entry prices prospectively before Phase 7 approval.
Promotion criteria: 30+ observations over 7+ calendar days.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class ShadowSignalObservation(SQLModel, table=True):
    """
    One record per observed signal. Created when a signal first meets criteria.
    Updated each cycle with latest market prices.
    NO positions. NO P&L. NO portfolio impact.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # ── Signal identity ───────────────────────────────────────────────────────
    market_id: str = Field(index=True)
    question: str = ""
    event_title: Optional[str] = None
    market_type: str = ""
    side: str = ""              # YES | NO | WATCH
    recommendation: str = ""
    confidence_score: int = 0
    model_prob: Optional[float] = None
    market_implied_prob: Optional[float] = None
    gap_pp: Optional[float] = None
    settlement_source: str = ""  # VERIFIED_NASA_GISTEMP | UNVERIFIED | etc.

    # ── Prices at FIRST observation (live real prices) ─────────────────────────
    first_seen_at: str = ""
    initial_best_bid: Optional[float] = None
    initial_best_ask: Optional[float] = None
    initial_mid_price: Optional[float] = None
    initial_spread: Optional[float] = None
    initial_liquidity: Optional[float] = None

    # ── Latest prices (updated each observation cycle) ─────────────────────────
    last_updated_at: Optional[str] = None
    latest_best_bid: Optional[float] = None
    latest_best_ask: Optional[float] = None
    latest_mid_price: Optional[float] = None
    latest_spread: Optional[float] = None

    # ── Directional move tracking (NOT portfolio P&L) ─────────────────────────
    # For YES signals: positive if market_mid rose since first observation
    # For NO signals:  positive if market_mid fell since first observation
    # This measures whether the market moved in the direction our signal predicted.
    directional_move_pct: Optional[float] = None

    # ── Market status ─────────────────────────────────────────────────────────
    is_active: bool = True          # market still open and accepting orders
    resolved: bool = False          # market has resolved
    resolved_yes: Optional[bool] = None   # True if YES won, False if NO won

    # ── Observation metadata ──────────────────────────────────────────────────
    times_seen: int = 1             # number of signal evaluation cycles where this signal appeared
    explanation: Optional[str] = None

    # Safety note — always present
    safety_note: str = (
        "SHADOW OBSERVATION ONLY. No position created. No capital debited. "
        "No portfolio P&L. directional_move_pct is market movement, not return on investment."
    )


class ShadowPriceSnapshot(SQLModel, table=True):
    """
    Price snapshot stored each time an observed signal is checked.
    Provides price history for the observation period.
    NOT trade records — pure market data.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    observation_id: Optional[int] = Field(default=None, index=True)
    market_id: str = Field(index=True)
    recorded_at: str = ""
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    mid_price: Optional[float] = None
    spread: Optional[float] = None
    liquidity: Optional[float] = None
    directional_move_pct: Optional[float] = None   # market move since first observation


class ShadowDailySummary(SQLModel, table=True):
    """
    One record per calendar day of shadow observation.
    Aggregates all observation activity for that day.
    Used to track the 7-day requirement for Phase 7 consideration.
    NO positions. NO P&L. Observation metadata only.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    date_utc: str = Field(index=True, unique=True)   # YYYY-MM-DD

    # Activity counts
    total_active_observations: int = 0     # unique markets observed this day
    new_observations_today: int = 0        # first time seen
    updated_observations_today: int = 0    # already existing, price updated
    snapshots_today: int = 0               # total price snapshots stored

    # Price quality metrics
    avg_spread_pct: Optional[float] = None          # average bid-ask spread % across all observations
    avg_liquidity_usd: Optional[float] = None
    markets_below_500_liquidity: int = 0            # count of observations filtered by liquidity

    # Directional movement metrics (NOT portfolio returns)
    avg_directional_move_pct: Optional[float] = None
    positive_moves_count: int = 0
    negative_moves_count: int = 0
    neutral_moves_count: int = 0

    # Recommendations seen
    enter_candidate_count: int = 0
    needs_check_count: int = 0
    watch_count: int = 0

    created_at: str = ""
    updated_at: str = ""
