"""Portfolio router — stub returning mock paper trading data. Live in Phase 7."""
from fastapi import APIRouter

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

MOCK_OPEN_POSITIONS = [
    {"id": 1, "market_id": "mock-001", "question": "Will July 2026 be the hottest July on record?",
     "side": "YES", "entry_price": 0.58, "current_price": 0.62, "size_usd": 2.00,
     "unrealised_pnl": 0.14, "unrealised_pct": 6.9, "stop_price": 0.493,
     "entry_time": "2026-05-28T10:30:00Z", "modules_triggered": "1,2"},
    {"id": 2, "market_id": "mock-004", "question": "Will 2026 be the hottest year on record globally?",
     "side": "YES", "entry_price": 0.68, "current_price": 0.71, "size_usd": 3.00,
     "unrealised_pnl": 0.13, "unrealised_pct": 4.4, "stop_price": 0.578,
     "entry_time": "2026-05-27T14:15:00Z", "modules_triggered": "1,2,4"},
]

MOCK_CLOSED_POSITIONS = [
    {"id": 0, "market_id": "mock-x01", "question": "Was May 2026 anomaly above +1.3°C?",
     "side": "YES", "entry_price": 0.54, "exit_price": 0.72, "size_usd": 2.00,
     "pnl_usd": 0.67, "pnl_pct": 33.3, "entry_time": "2026-05-10T09:00:00Z",
     "exit_time": "2026-05-25T16:00:00Z", "status": "closed"},
]

MOCK_EQUITY = [
    {"date": "2026-05-10", "capital": 100.00},
    {"date": "2026-05-15", "capital": 100.67},
    {"date": "2026-05-20", "capital": 101.10},
    {"date": "2026-05-25", "capital": 101.77},
    {"date": "2026-05-30", "capital": 102.04},
]


@router.get("/summary", summary="Portfolio summary stats")
def portfolio_summary():
    return {
        "starting_capital": 100.00,
        "current_capital": 102.04,
        "deployed_capital": 5.00,
        "available_capital": 97.04,
        "unrealised_pnl": 0.27,
        "realised_pnl": 1.77,
        "total_pnl": 2.04,
        "total_pnl_pct": 2.04,
        "open_positions": 2,
        "closed_positions": 1,
        "win_rate": 100.0,
        "data_source": "mock",
    }


@router.get("/positions/open", summary="Open paper positions")
def open_positions():
    return {"count": len(MOCK_OPEN_POSITIONS), "positions": MOCK_OPEN_POSITIONS, "data_source": "mock"}


@router.get("/positions/closed", summary="Closed paper positions")
def closed_positions():
    return {"count": len(MOCK_CLOSED_POSITIONS), "positions": MOCK_CLOSED_POSITIONS, "data_source": "mock"}


@router.get("/equity-curve", summary="Equity curve data points")
def equity_curve():
    return {"equity": MOCK_EQUITY, "data_source": "mock"}
