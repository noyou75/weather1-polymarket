"""
Backtest router — Phase 6.
Serves historical backtest results from SQLite.
BACKTEST ONLY — no paper trading, no real orders, no portfolio updates.
"""
import json
import logging
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models.backtest import BacktestRun, BacktestTrade, BacktestMetrics

logger = logging.getLogger("weather1.routers.backtest")
router = APIRouter(prefix="/backtest", tags=["Backtest"])

SAFETY_NOTE = (
    "BACKTEST ONLY. Estimated prices used — no historical Polymarket orderbook data. "
    "Past simulated performance does not guarantee future results. "
    "Data quality: see limitations in each response."
)


def _run_dict(r: BacktestRun) -> dict:
    return {
        "id": r.id, "run_at": r.run_at, "status": r.status,
        "total_signals": r.total_signals, "total_trades": r.total_trades,
        "win_rate_pct": r.win_rate_pct, "total_return_pct": r.total_return_pct,
        "max_drawdown_pct": r.max_drawdown_pct,
        "data_quality_rating": r.data_quality_rating, "readiness": r.readiness,
        "duration_ms": r.duration_ms, "safety_note": SAFETY_NOTE,
    }


def _metrics_dict(m: BacktestMetrics) -> dict:
    try:
        notes = json.loads(m.data_quality_notes or "[]")
    except Exception:
        notes = []
    try:
        lims = json.loads(m.limitations or "[]")
    except Exception:
        lims = []
    try:
        eq = json.loads(m.equity_curve or "[]")
    except Exception:
        eq = []
    return {
        "run_id": m.run_id,
        "performance": {
            "total_return_pct":          m.total_return_pct,
            "win_rate_pct":              m.win_rate_pct,
            "total_trades":              m.total_trades,
            "winning_trades":            m.winning_trades,
            "losing_trades":             m.losing_trades,
            "skipped_trades":            m.skipped_trades,
            "avg_return_per_trade_pct":  m.avg_return_per_trade_pct,
            "max_drawdown_pct":          m.max_drawdown_pct,
            "sharpe_estimate":           m.sharpe_estimate,
            "kill_switch_triggers":      m.kill_switch_triggers,
        },
        "module_accuracy": {
            "module1_classification_pct":  m.module1_accuracy_pct,
            "module2_direction_accuracy_pct": m.module2_direction_accuracy_pct,
            "module4_confirmation_rate_pct":  m.module4_confirmation_rate_pct,
        },
        "acceptance_criteria": {
            "pass_win_rate":     {"result": m.pass_win_rate,     "target": "≥52%",  "actual": f"{m.win_rate_pct:.1f}%"},
            "pass_max_drawdown": {"result": m.pass_max_drawdown, "target": "<12%",  "actual": f"{m.max_drawdown_pct:.1f}%"},
            "pass_sharpe":       {"result": m.pass_sharpe,       "target": ">0.8",  "actual": f"{m.sharpe_estimate:.2f}"},
            "pass_min_signals":  {"result": m.pass_min_signals,  "target": "≥30",   "actual": str(m.total_trades)},
            "pass_kill_switch":  {"result": m.pass_kill_switch,  "target": "0",     "actual": str(m.kill_switch_triggers)},
            "overall_pass":      m.overall_pass,
        },
        "quality": {
            "data_quality_rating": m.data_quality_rating,
            "readiness":           m.readiness,
            "data_quality_notes":  notes,
            "limitations":         lims,
        },
        "equity_curve": eq,
        "safety_note": SAFETY_NOTE,
    }


@router.get("/runs", summary="All backtest runs")
def list_runs(session: Session = Depends(get_session)):
    runs = session.exec(
        select(BacktestRun).order_by(BacktestRun.id.desc()).limit(20)  # type: ignore[arg-type]
    ).all()
    return {"count": len(runs), "runs": [_run_dict(r) for r in runs], "safety_note": SAFETY_NOTE}


@router.get("/latest", summary="Latest backtest run summary")
def latest_run(session: Session = Depends(get_session)):
    runs = session.exec(
        select(BacktestRun).order_by(BacktestRun.id.desc()).limit(1)  # type: ignore[arg-type]
    ).all()
    if not runs:
        return {
            "status": "never_run",
            "message": "No backtest run yet. POST /backtest/run-once to start.",
            "safety_note": SAFETY_NOTE,
        }
    return _run_dict(runs[0])


@router.get("/metrics", summary="Detailed metrics for latest backtest run")
def latest_metrics(session: Session = Depends(get_session)):
    runs = session.exec(
        select(BacktestRun).order_by(BacktestRun.id.desc()).limit(1)  # type: ignore[arg-type]
    ).all()
    if not runs:
        return {"status": "never_run", "safety_note": SAFETY_NOTE}
    m = session.exec(
        select(BacktestMetrics).where(BacktestMetrics.run_id == runs[0].id)
    ).first()
    if not m:
        return {"status": "no_metrics", "safety_note": SAFETY_NOTE}
    return _metrics_dict(m)


@router.get("/runs/{run_id}", summary="Specific backtest run detail")
def get_run(run_id: int, session: Session = Depends(get_session)):
    run = session.exec(select(BacktestRun).where(BacktestRun.id == run_id)).first()
    if not run:
        return {"error": f"Run {run_id} not found"}
    return _run_dict(run)


@router.get("/trades", summary="Simulated trade log for latest run")
def get_trades(limit: int = 100, session: Session = Depends(get_session)):
    runs = session.exec(
        select(BacktestRun).order_by(BacktestRun.id.desc()).limit(1)  # type: ignore[arg-type]
    ).all()
    if not runs:
        return {"count": 0, "trades": [], "safety_note": SAFETY_NOTE}
    trades = session.exec(
        select(BacktestTrade)
        .where(BacktestTrade.run_id == runs[0].id)
        .order_by(BacktestTrade.id)  # type: ignore[arg-type]
        .limit(limit)
    ).all()
    return {
        "count": len(trades),
        "run_id": runs[0].id,
        "safety_note": SAFETY_NOTE,
        "price_note": "Entry/exit prices are ESTIMATED — no historical Polymarket data available.",
        "trades": [
            {
                "id": t.id, "label": t.scenario_label, "year": t.test_year,
                "rank": t.target_rank, "months_in": t.entry_month,
                "side": t.signal_side, "gap_pp": t.gap_pp,
                "entry": t.entry_price, "exit": t.exit_price, "size": t.size_usd,
                "pnl_usd": t.pnl_usd, "pnl_pct": t.pnl_pct,
                "outcome": t.outcome, "reason": t.exit_reason,
                "direction_correct": t.direction_correct,
                "price_quality": t.price_quality, "notes": t.notes,
            }
            for t in trades
        ],
    }


@router.post("/run-once", summary="Run one backtest (local dev only, no real trades)")
def run_once():
    """Triggers historical backtest. No real trading. No portfolio updates."""
    from backtest.runner import run_backtest
    run = run_backtest()
    return {
        "run_id":             run.id,
        "status":             run.status,
        "total_signals":      run.total_signals,
        "total_trades":       run.total_trades,
        "win_rate_pct":       run.win_rate_pct,
        "total_return_pct":   run.total_return_pct,
        "max_drawdown_pct":   run.max_drawdown_pct,
        "data_quality":       run.data_quality_rating,
        "readiness":          run.readiness,
        "safety_note":        SAFETY_NOTE,
    }
