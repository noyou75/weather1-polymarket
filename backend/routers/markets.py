"""
Markets router — Phase 2: serves live data from SQLite (populated by Gamma API ingestion).
Falls back to clearly-labelled mock data if the DB is empty or not yet populated.
All endpoints are read-only.
"""
import logging
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models.markets import Market

logger = logging.getLogger("weather1.routers.markets")
router = APIRouter(prefix="/markets", tags=["Markets"])

# ── Mock fallback (labelled) — used only if DB is empty ──────────────────────
_MOCK_MARKETS = [
    {"market_id": "mock-001", "question": "Will July 2026 be the hottest July on record?",
     "event_title": "Global Temperature Records", "end_date": "2026-08-15",
     "yes_price": 0.62, "no_price": 0.38, "best_bid": 0.61, "best_ask": 0.63,
     "spread": 0.02, "liquidity": 18400, "volume": 240000, "volume_24hr": 3200,
     "signal_flag": "watch", "is_active": True, "is_closed": False,
     "accepting_orders": True, "data_source": "mock", "fetched_at": None},
    {"market_id": "mock-004", "question": "Will 2026 be the hottest year on record globally?",
     "event_title": "Global Temperature Records", "end_date": "2027-01-31",
     "yes_price": 0.71, "no_price": 0.29, "best_bid": 0.70, "best_ask": 0.72,
     "spread": 0.02, "liquidity": 42000, "volume": 460000, "volume_24hr": 5200,
     "signal_flag": "watch", "is_active": True, "is_closed": False,
     "accepting_orders": True, "data_source": "mock", "fetched_at": None},
]


def _market_to_dict(m: Market) -> dict:
    return {
        "market_id":       m.market_id,
        "condition_id":    m.condition_id,
        "question":        m.question,
        "event_title":     m.event_title,
        "slug":            m.slug,
        "end_date":        m.end_date,
        "yes_price":       m.yes_price,
        "no_price":        m.no_price,
        "best_bid":        m.best_bid,
        "best_ask":        m.best_ask,
        "spread":          m.spread,
        "last_trade_price": m.last_trade_price,
        "liquidity":       m.liquidity,
        "volume":          m.volume,
        "volume_24hr":     m.volume_24hr,
        "is_active":       m.is_active,
        "is_closed":       m.is_closed,
        "accepting_orders": m.accepting_orders,
        "neg_risk":        m.neg_risk,
        "signal_flag":     m.signal_flag,
        "data_source":     m.data_source,
        "fetched_at":      m.fetched_at,
        "resolution_source": m.resolution_source,
    }


@router.get("/", summary="All weather markets (live from DB or mock fallback)")
def list_markets(
    min_liquidity: float = 0,
    accepting_only: bool = False,
    session: Session = Depends(get_session),
):
    stmt = select(Market).where(
        Market.is_closed == False,  # noqa: E712
    )
    if accepting_only:
        stmt = stmt.where(Market.accepting_orders == True)  # noqa: E712
    markets = session.exec(stmt).all()

    if not markets:
        # DB empty — return labelled mock fallback
        fallback = _MOCK_MARKETS
        if min_liquidity > 0:
            fallback = [m for m in fallback if (m.get("liquidity") or 0) >= min_liquidity]
        return {
            "count": len(fallback),
            "data_source": "mock_fallback",
            "warning": "No live data yet. Run POST /ingestion/run-once to fetch from Gamma API.",
            "markets": fallback,
        }

    result = [_market_to_dict(m) for m in markets]
    if min_liquidity > 0:
        result = [m for m in result if (m.get("liquidity") or 0) >= min_liquidity]

    return {
        "count": len(result),
        "data_source": "gamma_api",
        "markets": result,
    }


@router.get("/weather", summary="Active weather markets only (alias for /markets)")
def weather_markets(
    min_liquidity: float = 0,
    session: Session = Depends(get_session),
):
    """Alias endpoint — all markets in DB are already weather-tagged."""
    return list_markets(min_liquidity=min_liquidity, accepting_only=False, session=session)


@router.get("/summary", summary="Market count summary")
def markets_summary(session: Session = Depends(get_session)):
    all_markets = session.exec(select(Market)).all()
    active = [m for m in all_markets if not m.is_closed]
    accepting = [m for m in active if m.accepting_orders]
    return {
        "total_in_db": len(all_markets),
        "active_open": len(active),
        "accepting_orders": len(accepting),
        "data_source": "gamma_api" if all_markets else "mock_fallback",
    }


@router.get("/{market_id}", summary="Single market detail")
def get_market(market_id: str, session: Session = Depends(get_session)):
    market = session.exec(
        select(Market).where(Market.market_id == market_id)
    ).first()
    if not market:
        # Check mock fallback
        mock = next((m for m in _MOCK_MARKETS if m["market_id"] == market_id), None)
        if mock:
            return {**mock, "data_source": "mock_fallback"}
        return {"error": f"Market {market_id} not found"}
    return _market_to_dict(market)
