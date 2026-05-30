"""Execution logs router — stub. Live logging active from Phase 2 onwards."""
from fastapi import APIRouter

router = APIRouter(prefix="/logs", tags=["Logs"])

MOCK_LOGS = [
    {"id": 1, "timestamp": "2026-05-30T08:00:00Z", "event_type": "data_fetch",
     "market_id": None, "detail": "Gamma API poll — 5 weather markets cached", "result": "ok", "module": "ingestion"},
    {"id": 2, "timestamp": "2026-05-30T08:01:00Z", "event_type": "signal_evaluated",
     "market_id": "mock-001", "detail": "Module 1 score: 0.81 | Module 2 gap: +14.2pp → recommendation: enter",
     "result": "ok", "module": "signal_engine"},
    {"id": 3, "timestamp": "2026-05-30T08:01:10Z", "event_type": "risk_check",
     "market_id": "mock-001", "detail": "Exposure check: $5/$35 | Daily loss: $0/$7 | Liquidity: OK",
     "result": "ok", "module": "risk_engine"},
    {"id": 4, "timestamp": "2026-05-30T08:01:11Z", "event_type": "paper_trade",
     "market_id": "mock-001", "detail": "Simulated BUY YES @ 0.58 + 1% slippage | Size: $2.00",
     "result": "ok", "module": "paper_simulator"},
    {"id": 5, "timestamp": "2026-05-30T08:15:00Z", "event_type": "signal_evaluated",
     "market_id": "mock-005", "detail": "Module 5 filter: liquidity $780 < $500 threshold — SKIPPED",
     "result": "skipped", "module": "signal_engine"},
]


@router.get("/", summary="Execution log with optional filters")
def get_logs(event_type: str = None, result: str = None, limit: int = 50):
    logs = MOCK_LOGS
    if event_type:
        logs = [l for l in logs if l["event_type"] == event_type]
    if result:
        logs = [l for l in logs if l["result"] == result]
    return {"count": len(logs[:limit]), "logs": logs[:limit], "data_source": "mock"}


@router.get("/summary", summary="Log event summary counts")
def log_summary():
    return {
        "total_events_today": 5,
        "by_type": {"data_fetch": 1, "signal_evaluated": 2, "risk_check": 1, "paper_trade": 1},
        "by_result": {"ok": 4, "skipped": 1, "blocked": 0, "error": 0},
        "data_source": "mock",
    }
