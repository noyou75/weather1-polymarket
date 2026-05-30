"""
Shadow signal observations router — Phase 6E/6F.
Read-only endpoints for the shadow observation layer.
NO positions. NO portfolio. NO paper trading.
Phase 6F: added /daily and /readiness endpoints.
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from database import get_session
from models.shadow import ShadowSignalObservation, ShadowPriceSnapshot, ShadowDailySummary

logger = logging.getLogger("weather1.routers.shadow")
router = APIRouter(prefix="/shadow", tags=["Shadow Observations"])

SAFETY_NOTE = (
    "SHADOW OBSERVATION ONLY. No positions. No capital. No portfolio P&L. "
    "directional_move_pct = market price move after signal — NOT investment return. "
    "Phase 7 always requires explicit written user approval."
)


def _obs_dict(o: ShadowSignalObservation, brief: bool = True) -> dict:
    return {
        "id":                   o.id,
        "market_id":            o.market_id,
        "question":             o.question[:100] + ("…" if len(o.question) > 100 else ""),
        "market_type":          o.market_type,
        "side":                 o.side,
        "recommendation":       o.recommendation,
        "confidence":           o.confidence_score,
        "gap_pp":               o.gap_pp,
        "settlement_source":    o.settlement_source,
        "first_seen_at":        o.first_seen_at,
        "last_updated_at":      o.last_updated_at,
        "times_seen":           o.times_seen,
        "initial_mid_price":    o.initial_mid_price,
        "initial_spread_pct":   round(o.initial_spread * 100, 2) if o.initial_spread else None,
        "initial_liquidity":    o.initial_liquidity,
        "latest_mid_price":     o.latest_mid_price,
        "directional_move_pct": o.directional_move_pct,
        "is_active":            o.is_active,
        **({"explanation": o.explanation,
            "model_prob": o.model_prob,
            "market_implied_prob": o.market_implied_prob,
            "event_title": o.event_title} if not brief else {}),
    }


@router.get("/status", summary="Shadow observation status + promotion criteria")
def shadow_status():
    from strategy.shadow_observer import get_shadow_status
    return get_shadow_status()


@router.get("/readiness", summary="Phase 7 readiness assessment (always BLOCKED without approval)")
def shadow_readiness():
    """
    Returns detailed Phase 7 readiness breakdown.
    Phase 7 is ALWAYS BLOCKED until explicit user written approval.
    This endpoint shows how far along the observation criteria are.
    """
    from strategy.shadow_observer import get_shadow_status
    s = get_shadow_status()
    return {
        "phase7_status":         s.get("phase7_status", "PHASE_7_BLOCKED"),
        "readiness_status":      s.get("readiness_status", "COLLECTING_SHADOW_DATA"),
        "days_until_review":     s.get("days_until_review", 7),
        "obs_until_review":      s.get("obs_until_review", 30),
        "calendar_days_observed": s.get("calendar_days_observed", 0),
        "total_observations":    s.get("total_observations", 0),
        "promotion_criteria":    s.get("promotion_criteria", {}),
        "blocking_note": (
            "Phase 7 (paper trading) will NEVER be automatically approved. "
            "Even when all criteria pass, explicit written user approval is required. "
            "Current status: PHASE_7_BLOCKED."
        ),
        "safety_note": SAFETY_NOTE,
    }


@router.get("/daily", summary="Daily summary table for shadow observation period")
def daily_summary(session: Session = Depends(get_session)):
    """Per-day breakdown of shadow observation activity."""
    rows = session.exec(
        select(ShadowDailySummary).order_by(ShadowDailySummary.date_utc)  # type: ignore[arg-type]
    ).all()
    return {
        "count":      len(rows),
        "safety_note": SAFETY_NOTE,
        "daily": [
            {
                "date":             r.date_utc,
                "active_obs":       r.total_active_observations,
                "new_obs":          r.new_observations_today,
                "updated_obs":      r.updated_observations_today,
                "snapshots":        r.snapshots_today,
                "avg_spread_pct":   round(r.avg_spread_pct, 2) if r.avg_spread_pct else None,
                "avg_dir_move_pct": round(r.avg_directional_move_pct, 3) if r.avg_directional_move_pct else None,
                "positive_moves":   r.positive_moves_count,
                "negative_moves":   r.negative_moves_count,
                "neutral_moves":    r.neutral_moves_count,
                "recommendations":  {
                    "enter_candidate": r.enter_candidate_count,
                    "needs_check":     r.needs_check_count,
                    "watch":           r.watch_count,
                },
            }
            for r in rows
        ],
    }


@router.get("/observations", summary="All shadow signal observations")
def list_observations(
    active_only: bool = Query(False),
    min_confidence: int = Query(0),
    limit: int = Query(100, le=500),
    session: Session = Depends(get_session),
):
    stmt = (
        select(ShadowSignalObservation)
        .order_by(ShadowSignalObservation.directional_move_pct.desc())  # type: ignore[arg-type]
        .limit(limit)
    )
    obs = session.exec(stmt).all()
    filtered = [o for o in obs
                if (not active_only or o.is_active)
                and o.confidence_score >= min_confidence]
    return {
        "count":       len(filtered),
        "safety_note": SAFETY_NOTE,
        "observations": [_obs_dict(o) for o in filtered],
    }


@router.get("/latest", summary="Latest active shadow observations summary")
def latest_observations(session: Session = Depends(get_session)):
    from strategy.shadow_observer import get_shadow_status
    obs = session.exec(
        select(ShadowSignalObservation)
        .where(ShadowSignalObservation.is_active == True)  # noqa: E712
        .order_by(ShadowSignalObservation.directional_move_pct.desc())  # type: ignore[arg-type]
        .limit(20)
    ).all()

    dir_moves = [o.directional_move_pct for o in obs if o.directional_move_pct is not None]
    avg_move  = sum(dir_moves) / len(dir_moves) if dir_moves else None

    top_pos = sorted([o for o in obs if (o.directional_move_pct or 0) > 0],
                     key=lambda x: -(x.directional_move_pct or 0))[:3]
    top_neg = sorted([o for o in obs if (o.directional_move_pct or 0) < 0],
                     key=lambda x: (x.directional_move_pct or 0))[:3]

    status = get_shadow_status()
    return {
        "active_observations":      len(obs),
        "avg_directional_move_pct": round(avg_move, 3) if avg_move is not None else None,
        "phase7_status":            status.get("phase7_status", "PHASE_7_BLOCKED"),
        "top_positive_moves":       [_obs_dict(o) for o in top_pos],
        "top_negative_moves":       [_obs_dict(o) for o in top_neg],
        "observations":             [_obs_dict(o) for o in obs],
        "safety_note":              SAFETY_NOTE,
    }


@router.get("/observations/{obs_id}", summary="Single observation detail with price history")
def get_observation(obs_id: int, session: Session = Depends(get_session)):
    obs = session.exec(
        select(ShadowSignalObservation).where(ShadowSignalObservation.id == obs_id)
    ).first()
    if not obs:
        return {"error": f"Observation {obs_id} not found"}
    snaps = session.exec(
        select(ShadowPriceSnapshot)
        .where(ShadowPriceSnapshot.observation_id == obs_id)
        .order_by(ShadowPriceSnapshot.id)  # type: ignore[arg-type]
    ).all()
    return {
        **_obs_dict(obs, brief=False),
        "price_history": [
            {"recorded_at": s.recorded_at, "mid_price": s.mid_price,
             "spread": s.spread, "directional_move_pct": s.directional_move_pct}
            for s in snaps
        ],
    }


@router.post("/run-once", summary="Run shadow observation cycle (local dev, no positions)")
def run_once():
    """
    One shadow observation cycle. SAFETY: No positions. No capital. Read-only.
    Hardened: same market never creates duplicate rows — updates existing + adds snapshot.
    """
    from strategy.shadow_observer import run_shadow_observation
    result = run_shadow_observation()
    return {**result, "safety_note": SAFETY_NOTE}
