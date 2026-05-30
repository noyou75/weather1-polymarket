"""
Top wallet model — Phase 3.
Populated from the local polymarket_weather_top100.html snapshot.
Static intelligence layer for Module 4 (confirmation signal).
No live polling, no private keys, no copy-trading.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class TopWallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # ── Leaderboard identity ──────────────────────────────────────────────────
    rank: int = Field(index=True)
    wallet_address: str = Field(index=True, unique=True)
    username: Optional[str] = None
    x_username: Optional[str] = None
    verified: bool = False

    # ── Performance metrics ───────────────────────────────────────────────────
    pnl_usd: float = 0.0
    volume_usd: float = 0.0
    efficiency_pct: float = 0.0           # (pnl / volume) * 100

    # ── Strategy classification ───────────────────────────────────────────────
    strategies: Optional[str] = None      # JSON array string: '["Sharp Selector","Multi-Wallet"]'
    strategy_detail: Optional[str] = None # Full strategy analysis text

    # ── Module 4 watchlist flags ──────────────────────────────────────────────
    on_watchlist: bool = False            # True for top-efficiency traders used in Module 4
    watchlist_reason: Optional[str] = None

    # ── Snapshot metadata ─────────────────────────────────────────────────────
    snapshot_date: str = "2026-05"        # Month of leaderboard snapshot
    source_file: str = "polymarket_weather_top100.html"
