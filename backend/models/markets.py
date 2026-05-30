"""
Market metadata model — Phase 2: populated from Polymarket Gamma API (read-only).
All price fields come directly from the Gamma API response; no CLOB API needed.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class Market(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # ── Polymarket identifiers ────────────────────────────────────────────────
    market_id: str = Field(index=True, unique=True)   # Gamma integer id as string
    condition_id: Optional[str] = Field(default=None, index=True)  # 0x… on-chain ID
    slug: Optional[str] = None
    question: str = ""
    description: Optional[str] = None
    resolution_source: Optional[str] = None

    # ── Outcomes ─────────────────────────────────────────────────────────────
    outcomes: Optional[str] = None           # JSON string e.g. '["Yes","No"]'
    outcome_prices: Optional[str] = None     # JSON string e.g. '["0.32","0.68"]'
    clob_token_id_yes: Optional[str] = None  # CLOB token ID for YES outcome
    clob_token_id_no: Optional[str] = None   # CLOB token ID for NO outcome

    # ── Live price data (from Gamma API, refreshed each ingest cycle) ─────────
    yes_price: Optional[float] = None        # outcomePrices[0] or lastTradePrice
    no_price: Optional[float] = None         # outcomePrices[1]
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    spread: Optional[float] = None           # fraction of mid-price
    last_trade_price: Optional[float] = None

    # ── Volume & liquidity ────────────────────────────────────────────────────
    liquidity: Optional[float] = None
    volume: Optional[float] = None
    volume_24hr: Optional[float] = None

    # ── Market status ─────────────────────────────────────────────────────────
    category: str = "weather"
    is_active: bool = True
    is_closed: bool = False
    accepting_orders: bool = False
    neg_risk: bool = False

    # ── Timing ───────────────────────────────────────────────────────────────
    end_date: Optional[str] = None           # ISO datetime string
    start_date: Optional[str] = None
    last_updated: Optional[str] = None       # Gamma API updatedAt
    fetched_at: Optional[str] = None         # When we last fetched this record

    # ── Parent event context ──────────────────────────────────────────────────
    event_title: Optional[str] = None
    event_slug: Optional[str] = None

    # ── Dashboard helpers ──────────────────────────────────────────────────────
    signal_flag: Optional[str] = None        # "green" | "watch" | None
    data_source: str = "gamma_api"           # "gamma_api" | "mock"
