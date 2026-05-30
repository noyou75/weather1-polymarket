"""
Market price snapshot — one row per ingest cycle per market.
Provides price history for future charting. Phase 2+.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class MarketPrice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: str = Field(index=True)
    fetched_at: str = ""          # ISO timestamp of this snapshot
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    spread: Optional[float] = None
    last_trade_price: Optional[float] = None
    liquidity: Optional[float] = None
    volume_24hr: Optional[float] = None
