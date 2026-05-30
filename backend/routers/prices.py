"""
Prices router — Phase 2: latest prices per market from SQLite.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models.market_prices import MarketPrice

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get("/latest", summary="Latest price snapshot for each market")
def latest_prices(session: Session = Depends(get_session)):
    """
    Returns the most recent price snapshot for every market.
    Uses a subquery to get max id per market_id.
    """
    all_prices = session.exec(
        select(MarketPrice).order_by(MarketPrice.id.desc())  # type: ignore[arg-type]
    ).all()

    # Deduplicate to one row per market_id (latest)
    seen: set[str] = set()
    latest: list[dict] = []
    for p in all_prices:
        if p.market_id not in seen:
            seen.add(p.market_id)
            latest.append({
                "market_id":        p.market_id,
                "fetched_at":       p.fetched_at,
                "yes_price":        p.yes_price,
                "no_price":         p.no_price,
                "best_bid":         p.best_bid,
                "best_ask":         p.best_ask,
                "spread":           p.spread,
                "last_trade_price": p.last_trade_price,
                "liquidity":        p.liquidity,
                "volume_24hr":      p.volume_24hr,
            })

    return {
        "count": len(latest),
        "data_source": "gamma_api" if latest else "no_data",
        "prices": latest,
    }


@router.get("/{market_id}/history", summary="Price history for a specific market")
def price_history(market_id: str, limit: int = 50, session: Session = Depends(get_session)):
    rows = session.exec(
        select(MarketPrice)
        .where(MarketPrice.market_id == market_id)
        .order_by(MarketPrice.id.desc())  # type: ignore[arg-type]
        .limit(limit)
    ).all()
    return {
        "market_id": market_id,
        "count": len(rows),
        "history": [
            {
                "fetched_at": r.fetched_at,
                "yes_price": r.yes_price,
                "best_bid": r.best_bid,
                "best_ask": r.best_ask,
                "spread": r.spread,
                "liquidity": r.liquidity,
            }
            for r in rows
        ],
    }
