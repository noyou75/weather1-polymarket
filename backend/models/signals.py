"""
Signal models — Phase 5.
Analytical signals only. No trades. No portfolio updates. No order code.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class SignalRun(SQLModel, table=True):
    """One record per signal evaluation run."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_at: str = ""
    status: str = "running"          # "running" | "ok" | "error"
    markets_evaluated: int = 0
    enter_candidates: int = 0        # ENTER_CANDIDATE + NEEDS_SETTLEMENT_SOURCE_CHECK
    watch_count: int = 0             # WATCH + NEEDS_MORE_DATA
    skip_count: int = 0              # all SKIP_* combined
    duration_ms: int = 0
    recommendation_counts: Optional[str] = None   # JSON str of counter dict
    errors: int = 0


class Signal(SQLModel, table=True):
    """
    One signal per market per run.
    ANALYTICAL ONLY — no trade execution, no portfolio impact.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: Optional[int] = Field(default=None, index=True)    # FK to SignalRun

    # ── Market identity ───────────────────────────────────────────────────────
    market_id: str = Field(index=True)
    question: str = ""
    event_title: Optional[str] = None
    market_type: str = ""            # from Module 1

    # ── Price / probability ───────────────────────────────────────────────────
    side: str = "WATCH"              # "YES" | "NO" | "WATCH" | "SKIP"
    market_implied_prob: Optional[float] = None   # mid-price
    model_estimated_prob: Optional[float] = None  # Module 2 estimate
    probability_gap_pp: Optional[float] = None    # model - market (pp)

    # ── Confidence & modules ──────────────────────────────────────────────────
    confidence_score: int = 0        # 0–100 (capped at 60 if settlement unverified)
    module1_result: str = ""         # market type string
    module2_result: str = ""         # "good" | "partial" | "insufficient"
    module4_result: str = ""         # "confirmed" | "not_confirmed"
    module5_result: str = ""         # "pass" | SKIP_* reason

    # ── Status flags ──────────────────────────────────────────────────────────
    liquidity_ok: bool = False
    weather_data_fresh: bool = False
    settlement_source_verified: bool = False   # always False in Phase 5

    # ── Output ────────────────────────────────────────────────────────────────
    recommendation: str = ""         # ENTER_CANDIDATE | WATCH | SKIP_* | NEEDS_*
    explanation: Optional[str] = None
    created_at: str = ""

    # Phase 5 safety note — always present
    safety_note: str = (
        "ANALYTICAL SIGNAL ONLY. No trade placed. No paper portfolio updated. "
        "Settlement source must be verified before any trading use."
    )
