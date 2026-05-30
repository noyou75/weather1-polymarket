"""Paper trading position model — populated in Phase 7."""
from typing import Optional
from sqlmodel import Field, SQLModel


class Position(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: str = Field(index=True)
    question: str
    side: str                               # "YES" | "NO"
    entry_price: float
    current_price: Optional[float] = None
    size_usd: float                         # Paper dollars wagered
    status: str = "open"                    # "open" | "closed"
    entry_time: str = ""                    # ISO datetime
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    pnl_usd: Optional[float] = None
    pnl_pct: Optional[float] = None
    stop_price: Optional[float] = None     # –15% of entry
    modules_triggered: Optional[str] = None # "1,2" | "1" | "2"
    notes: Optional[str] = None
