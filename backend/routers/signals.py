"""
Signals router — Phase 5.
Serves analytical signals from SQLite.
IMPORTANT: Signals are informational only. No trades. No orders.
"""
import json
import logging
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import get_session
from models.signals import Signal, SignalRun

logger = logging.getLogger("weather1.routers.signals")
router = APIRouter(prefix="/signals", tags=["Signals"])

SAFETY_NOTE = (
    "ANALYTICAL SIGNALS ONLY. No trade placed. No paper portfolio updated. "
    "No real orders. Settlement source must be verified before any trading use."
)


def _sig_dict(s: Signal, include_explanation: bool = True) -> dict:
    return {
        "id":                   s.id,
        "run_id":               s.run_id,
        "market_id":            s.market_id,
        "question":             s.question[:120] + ("…" if len(s.question) > 120 else ""),
        "event_title":          s.event_title,
        "market_type":          s.market_type,
        "side":                 s.side,
        "market_implied_prob":  s.market_implied_prob,
        "model_estimated_prob": s.model_estimated_prob,
        "probability_gap_pp":   s.probability_gap_pp,
        "confidence_score":     s.confidence_score,
        "module1":              s.module1_result,
        "module2":              s.module2_result,
        "module4":              s.module4_result,
        "module5":              s.module5_result,
        "liquidity_ok":         s.liquidity_ok,
        "weather_fresh":        s.weather_data_fresh,
        "settlement_verified":  s.settlement_source_verified,
        "recommendation":       s.recommendation,
        "explanation":          (s.explanation or "")[:300] if include_explanation else None,
        "created_at":           s.created_at,
        "safety_note":          SAFETY_NOTE,
    }


@router.get("/status", summary="Signal engine status")
def signals_status(session: Session = Depends(get_session)):
    runs = session.exec(
        select(SignalRun).order_by(SignalRun.id.desc()).limit(1)  # type: ignore[arg-type]
    ).all()
    last = runs[0] if runs else None

    total_signals = len(session.exec(select(Signal)).all())

    return {
        "last_run_at":       last.run_at if last else None,
        "last_status":       last.status if last else "never_run",
        "last_markets_eval": last.markets_evaluated if last else 0,
        "last_enter_cands":  last.enter_candidates if last else 0,
        "last_watch":        last.watch_count if last else 0,
        "last_skip":         last.skip_count if last else 0,
        "last_duration_ms":  last.duration_ms if last else 0,
        "total_signals_in_db": total_signals,
        "safety_note":       SAFETY_NOTE,
    }


@router.get("/latest", summary="Latest signals from most recent run")
def latest_signals(
    recommendation: str = Query("", description="Filter by recommendation e.g. ENTER_CANDIDATE"),
    market_type: str = Query("", description="Filter by market type e.g. annual_temp"),
    min_confidence: int = Query(0, description="Minimum confidence score"),
    liquidity_ok: bool | None = Query(None),
    limit: int = Query(100, le=500),
    session: Session = Depends(get_session),
):
    # Get latest run id
    runs = session.exec(
        select(SignalRun).order_by(SignalRun.id.desc()).limit(1)  # type: ignore[arg-type]
    ).all()
    if not runs:
        return {"count": 0, "run_id": None, "signals": [], "safety_note": SAFETY_NOTE}

    latest_run = runs[0]

    stmt = select(Signal).where(
        Signal.run_id == latest_run.id,
        Signal.confidence_score >= min_confidence,
    )
    if recommendation:
        stmt = stmt.where(Signal.recommendation == recommendation)
    if market_type:
        stmt = stmt.where(Signal.market_type == market_type)
    if liquidity_ok is not None:
        stmt = stmt.where(Signal.liquidity_ok == liquidity_ok)

    stmt = stmt.order_by(Signal.confidence_score.desc()).limit(limit)  # type: ignore[arg-type]
    signals = session.exec(stmt).all()

    return {
        "count":      len(signals),
        "run_id":     latest_run.id,
        "run_at":     latest_run.run_at,
        "run_status": latest_run.status,
        "safety_note": SAFETY_NOTE,
        "signals":    [_sig_dict(s) for s in signals],
    }


@router.get("/summary", summary="Recommendation distribution from latest run")
def signal_summary(session: Session = Depends(get_session)):
    runs = session.exec(
        select(SignalRun).order_by(SignalRun.id.desc()).limit(1)  # type: ignore[arg-type]
    ).all()
    if not runs:
        return {"status": "never_run", "safety_note": SAFETY_NOTE}
    r = runs[0]
    try:
        counts = json.loads(r.recommendation_counts or "{}")
    except Exception:
        counts = {}
    return {
        "run_at":       r.run_at,
        "status":       r.status,
        "evaluated":    r.markets_evaluated,
        "enter_candidates": r.enter_candidates,
        "watch":        r.watch_count,
        "skip":         r.skip_count,
        "by_recommendation": counts,
        "duration_ms":  r.duration_ms,
        "safety_note":  SAFETY_NOTE,
    }


@router.get("/{signal_id}", summary="Single signal detail")
def get_signal(signal_id: int, session: Session = Depends(get_session)):
    sig = session.exec(select(Signal).where(Signal.id == signal_id)).first()
    if not sig:
        return {"error": f"Signal {signal_id} not found"}
    return _sig_dict(sig, include_explanation=True)


@router.post("/run-once", summary="Trigger one signal evaluation run (local dev only, no trades)")
def run_once():
    """
    Triggers one complete signal evaluation run.
    ANALYTICAL ONLY — no trades, no portfolio updates, no real orders.
    Local development use only.
    """
    logger.info("Manual signal run triggered via /signals/run-once")
    from strategy.engine import run_signal_evaluation
    run = run_signal_evaluation()
    return {
        "run_id":       run.id,
        "status":       run.status,
        "evaluated":    run.markets_evaluated,
        "enter_candidates": run.enter_candidates,
        "watch":        run.watch_count,
        "skip":         run.skip_count,
        "duration_ms":  run.duration_ms,
        "safety_note":  SAFETY_NOTE,
    }
