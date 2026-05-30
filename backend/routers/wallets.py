"""
Wallets router — Phase 3.
Serves Top 100 weather trader data from SQLite (parsed from local HTML snapshot).
All data is static intelligence — no live wallet polling, no copy-trading.

Safety reminder:
- No wallet private keys.
- No wallet authentication.
- No live copy-trading.
- No real orders.
- Module 4 confirmation only — never a primary trade trigger.
"""
import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import get_session
from models.top_wallets import TopWallet

logger = logging.getLogger("weather1.routers.wallets")
router = APIRouter(prefix="/wallets", tags=["Wallets"])

# ── Constants from Phase 0 plan ───────────────────────────────────────────────
TOP50_PNL_THRESHOLD = 21940.06   # vip68, rank #50
WATCHLIST_MIN_EFFICIENCY = 8.0


def _wallet_to_dict(w: TopWallet, include_detail: bool = False) -> dict:
    try:
        strats = json.loads(w.strategies or "[]")
    except Exception:
        strats = []
    record = {
        "rank":             w.rank,
        "wallet_address":   w.wallet_address,
        "username":         w.username,
        "x_username":       w.x_username,
        "verified":         w.verified,
        "pnl_usd":          w.pnl_usd,
        "volume_usd":       w.volume_usd,
        "efficiency_pct":   w.efficiency_pct,
        "strategies":       strats,
        "on_watchlist":     w.on_watchlist,
        "watchlist_reason": w.watchlist_reason,
        "snapshot_date":    w.snapshot_date,
    }
    if include_detail:
        record["strategy_detail"] = w.strategy_detail
    return record


@router.get("/top", summary="All Top 100 weather traders")
def list_top_wallets(
    min_efficiency: float = Query(0.0, description="Minimum efficiency %"),
    strategy: str = Query("", description="Filter by strategy tag e.g. 'Sharp Selector'"),
    max_rank: int = Query(100, description="Maximum rank to include"),
    search: str = Query("", description="Search by username or wallet address"),
    session: Session = Depends(get_session),
):
    wallets = session.exec(
        select(TopWallet).order_by(TopWallet.rank)
    ).all()

    if not wallets:
        return {
            "count": 0,
            "data_source": "not_imported",
            "warning": "No wallets in DB. POST /wallets/import-top100 to parse the snapshot.",
            "wallets": [],
        }

    result = []
    for w in wallets:
        if w.rank > max_rank:
            continue
        if w.efficiency_pct < min_efficiency:
            continue
        if strategy:
            try:
                strats = json.loads(w.strategies or "[]")
            except Exception:
                strats = []
            if strategy not in strats:
                continue
        if search:
            q = search.lower()
            if q not in (w.username or "").lower() and q not in w.wallet_address.lower():
                continue
        result.append(_wallet_to_dict(w))

    return {
        "count": len(result),
        "total_in_db": len(wallets),
        "data_source": "local_snapshot",
        "snapshot_date": "2026-05",
        "wallets": result,
    }


@router.get("/top/{wallet_address}", summary="Single wallet detail with full strategy notes")
def get_wallet(wallet_address: str, session: Session = Depends(get_session)):
    wallet = session.exec(
        select(TopWallet).where(TopWallet.wallet_address == wallet_address)
    ).first()
    if not wallet:
        # Try by username (convenience)
        wallet = session.exec(
            select(TopWallet).where(TopWallet.username == wallet_address)
        ).first()
    if not wallet:
        return {"error": f"Wallet '{wallet_address}' not found in top 100 snapshot"}
    return _wallet_to_dict(wallet, include_detail=True)


@router.get("/strategy-types", summary="Strategy type distribution across Top 100")
def strategy_distribution(session: Session = Depends(get_session)):
    from ingestion.top_wallets import get_strategy_distribution
    dist = get_strategy_distribution()
    total = session.exec(select(TopWallet)).all()
    return {
        "total_wallets": len(total),
        "distribution": dist,
        "data_source": "local_snapshot",
    }


@router.get("/watchlist", summary="Module 4 watchlist — high-efficiency Sharp Selectors")
def get_watchlist(session: Session = Depends(get_session)):
    """
    Returns traders on the Module 4 confirmation watchlist.
    Criteria: efficiency > 8% AND Sharp Selector strategy.
    These wallets can CONFIRM an existing signal — they never trigger a trade alone.
    """
    wallets = session.exec(
        select(TopWallet)
        .where(TopWallet.on_watchlist == True)  # noqa: E712
        .order_by(TopWallet.efficiency_pct.desc())  # type: ignore[arg-type]
    ).all()
    return {
        "count": len(wallets),
        "criteria": f"efficiency > {WATCHLIST_MIN_EFFICIENCY}% AND Sharp Selector strategy",
        "module": "Module 4 — Confirmation Signal Only",
        "safety_note": "These wallets confirm signals — they never trigger independent trades",
        "wallets": [_wallet_to_dict(w, include_detail=False) for w in wallets],
    }


@router.get("/summary", summary="Top 100 leaderboard summary stats")
def wallet_summary(session: Session = Depends(get_session)):
    wallets = session.exec(select(TopWallet).order_by(TopWallet.rank)).all()
    if not wallets:
        return {"status": "not_imported", "wallets": 0}

    watchlist = [w for w in wallets if w.on_watchlist]
    rank50 = next((w for w in wallets if w.rank == 50), None)
    top_eff = sorted(wallets, key=lambda w: w.efficiency_pct, reverse=True)[:3]

    dist: dict[str, int] = {}
    for w in wallets:
        try:
            for s in json.loads(w.strategies or "[]"):
                dist[s] = dist.get(s, 0) + 1
        except Exception:
            pass

    return {
        "total_wallets": len(wallets),
        "watchlist_size": len(watchlist),
        "top50_pnl_threshold": rank50.pnl_usd if rank50 else TOP50_PNL_THRESHOLD,
        "top50_efficiency_threshold": rank50.efficiency_pct if rank50 else None,
        "top3_by_efficiency": [
            {"rank": w.rank, "username": w.username, "efficiency_pct": w.efficiency_pct}
            for w in top_eff
        ],
        "strategy_distribution": dist,
        "data_source": "local_snapshot",
        "snapshot_date": "2026-05",
    }


@router.post("/import-top100", summary="Parse local top100 HTML and store in DB (local file only)")
def import_top100():
    """
    Parses the local polymarket_weather_top100.html file.
    Reads from: Weather1/data/raw/polymarket_weather_top100.html
    No network calls. No external write operations.
    """
    from ingestion.top_wallets import run_top100_import
    result = run_top100_import()
    return result
