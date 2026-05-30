"""
Weather1 Signal Engine — Phase 5 / v1.1 calibration (Phase 6C).

IMPORTANT: This engine generates ANALYTICAL SIGNALS ONLY.
- No trades are placed.
- No paper portfolio is updated.
- No real orders are sent.
- No private keys are used.
- No Polymarket write endpoints are called.

v1.1 changes (Phase 6C):
- Rank-2+ annual markets → SKIP_UNSUPPORTED_TYPE (classified as annual_rank_lower by Module 1)
- WATCH gap threshold raised: 10pp (was 8pp)
- ENTER_CANDIDATE gap threshold raised: 15pp (was 8pp)
- Settlement source hard gate: ENTER requires verified source (still unverified in Phase 6C)
- Near-expiry city markets: 24h → SKIP; 48h → WATCH_ONLY

Signal flow:
  Module 5 (Liquidity gate) → Module 1 (Classification) → Module 2 (Probability gap)
  → Module 4 (Wallet confirmation) → Confidence score → Recommendation
"""
import json
import logging
import time
from datetime import datetime, timezone

from sqlmodel import Session, select

from database import engine
from models.markets import Market
from models.signals import Signal, SignalRun
from strategy import module1_market_type as m1
from strategy import module2_probability_gap as m2
from strategy import module4_wallet_confirmation as m4
from strategy import module5_liquidity as m5

logger = logging.getLogger("weather1.strategy.engine")

# v1.1 gap thresholds (raised from Phase 5 values)
MIN_GAP_WATCH  = 10.0   # pp — was 8pp in v1.0; removes 5pp false positives
MIN_GAP_ENTER  = 15.0   # pp — was 8pp in v1.0; requires stronger signal

# Confidence thresholds
THRESHOLD_ENTER  = 55
THRESHOLD_WATCH  = 30

# Settlement source unverified → cap at 60
# Phase 6D: annual_temp and global_monthly_temp are now VERIFIED → no cap applies
SETTLEMENT_UNVERIFIED_CAP = 60

# How many markets to evaluate per run (avoid very long runs)
MAX_MARKETS_PER_RUN = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _recommendation(
    confidence: int,
    gap_pp: float | None,
    m5_result: m5.LiquidityResult,
    m1_type: str,
    m2_result: m2.ProbabilityResult,
    settlement_verified: bool,
) -> str:
    """Determine final recommendation from all module outputs."""
    # Liquidity failures (hard gates)
    if not m5_result.passed:
        return m5_result.recommendation

    # Unsupported market type
    if m1_type not in m1.SUPPORTED_TYPES:
        return "SKIP_UNSUPPORTED_TYPE"

    # Settlement source never verified in Phase 5
    if not settlement_verified:
        effective_cap = SETTLEMENT_UNVERIFIED_CAP
    else:
        effective_cap = 100

    effective_conf = min(confidence, effective_cap)

    # v1.1: rank-2+ annual markets now classified as annual_rank_lower → already caught above
    # City temp markets: settlement source is NWS (not confirmed for Polymarket)
    if m1_type == m1.TYPE_CITY_STATION_TEMP and not settlement_verified:
        # v1.1: raise threshold for ENTER check; settlement still unverified
        if effective_conf >= THRESHOLD_ENTER and gap_pp is not None and abs(gap_pp) >= MIN_GAP_ENTER:
            return "NEEDS_SETTLEMENT_SOURCE_CHECK"
        # v1.1: WATCH requires gap >= MIN_GAP_WATCH (10pp)
        if effective_conf >= THRESHOLD_WATCH and gap_pp is not None and abs(gap_pp) >= MIN_GAP_WATCH:
            return "WATCH"
        return "NEEDS_MORE_DATA"

    # Global temp markets
    if m2_result.data_quality == "insufficient" or m2_result.estimated_prob is None:
        return "NEEDS_MORE_DATA"

    # v1.1: ENTER requires gap >= 15pp (hard gate) AND settlement verified (still unverified)
    if effective_conf >= THRESHOLD_ENTER and gap_pp is not None and abs(gap_pp) >= MIN_GAP_ENTER:
        return "ENTER_CANDIDATE" if settlement_verified else "NEEDS_SETTLEMENT_SOURCE_CHECK"

    # v1.1: WATCH requires gap >= 10pp (was no gap requirement in v1.0)
    if effective_conf >= THRESHOLD_WATCH and gap_pp is not None and abs(gap_pp) >= MIN_GAP_WATCH:
        return "WATCH"

    # Below watch threshold or gap too small
    if gap_pp is not None and abs(gap_pp) < MIN_GAP_WATCH:
        return "NEEDS_MORE_DATA"

    return "NEEDS_MORE_DATA"


def evaluate_market(market: Market, run_id: int) -> Signal:
    """
    Evaluate a single market through all signal modules.
    Returns a Signal object (not yet committed to DB).
    """
    now = _now_iso()

    # ── Module 5: Liquidity gate (first — fail fast) ──────────────────────────
    liq = m5.check(
        liquidity=market.liquidity,
        spread=market.spread,
        best_bid=market.best_bid,
        best_ask=market.best_ask,
        end_date=market.end_date,
        fetched_at=market.fetched_at,
    )
    implied_prob = m5.implied_probability(market.best_bid, market.best_ask)

    if not liq.passed:
        return Signal(
            run_id=run_id,
            market_id=market.market_id,
            question=market.question or "",
            event_title=market.event_title,
            market_type="unknown",
            side="SKIP",
            market_implied_prob=implied_prob,
            model_estimated_prob=None,
            probability_gap_pp=None,
            confidence_score=0,
            module1_result="not_evaluated",
            module2_result="not_evaluated",
            module4_result="not_evaluated",
            module5_result=liq.recommendation,
            liquidity_ok=False,
            weather_data_fresh=False,
            settlement_source_verified=False,
            recommendation=liq.recommendation,
            explanation=liq.reason,
            created_at=now,
        )

    # ── Module 1: Market type classification ──────────────────────────────────
    cl = m1.classify_market(
        question=market.question or "",
        event_title=market.event_title or "",
        end_date=market.end_date,
    )

    if cl.market_type not in m1.SUPPORTED_TYPES:
        return Signal(
            run_id=run_id,
            market_id=market.market_id,
            question=market.question or "",
            event_title=market.event_title,
            market_type=cl.market_type,
            side="SKIP",
            market_implied_prob=implied_prob,
            model_estimated_prob=None,
            probability_gap_pp=None,
            confidence_score=0,
            module1_result=cl.market_type,
            module2_result="not_evaluated",
            module4_result="not_evaluated",
            module5_result="pass",
            liquidity_ok=True,
            weather_data_fresh=True,
            settlement_source_verified=False,
            recommendation="SKIP_UNSUPPORTED_TYPE",
            explanation=cl.skip_reason or f"Type '{cl.market_type}' not supported in Phase 5",
            created_at=now,
        )

    # ── Module 2: Probability gap estimation ─────────────────────────────────
    m2r = m2.estimate(
        market_type=cl.market_type,
        question=market.question or "",
        cl=cl,
        market_implied_prob=implied_prob,
    )

    # ── Module 4: Wallet confirmation (static) ────────────────────────────────
    m4r = m4.check(market_type=cl.market_type, question=market.question or "")

    # ── Confidence scoring ────────────────────────────────────────────────────
    # Base: 20 points for supported market type
    # Module 2: 0–45 points from probability gap and data quality
    # Module 4: 0–15 points from wallet confirmation
    # Settlement cap: max 60 if not verified

    type_points = 20 if cl.market_type in m1.SUPPORTED_TYPES else 0
    confidence = type_points + m2r.confidence_contribution + m4r.confidence_contribution

    if not m2r.settlement_verified:
        confidence = min(confidence, SETTLEMENT_UNVERIFIED_CAP)

    # ── Direction (side) ─────────────────────────────────────────────────────
    if m2r.gap_pp is not None:
        if m2r.gap_pp >= 4:
            side = "YES"      # model thinks market underprices YES
        elif m2r.gap_pp <= -4:
            side = "NO"       # model thinks market underprices NO
        else:
            side = "WATCH"    # gap too small to have directional conviction
    else:
        side = "WATCH"

    # ── Recommendation ────────────────────────────────────────────────────────
    rec = _recommendation(
        confidence=confidence,
        gap_pp=m2r.gap_pp,
        m5_result=liq,
        m1_type=cl.market_type,
        m2_result=m2r,
        settlement_verified=m2r.settlement_verified,
    )

    # ── Explanation ───────────────────────────────────────────────────────────
    explanation_parts = [m2r.explanation]
    if m4r.confirmed:
        explanation_parts.append(f"Module 4: {m4r.rationale}")
    if liq.warn_wide_spread:
        explanation_parts.append(f"Warning: spread {liq.spread_pct} > 2% (not blocking).")
    explanation = " | ".join(p for p in explanation_parts if p)

    return Signal(
        run_id=run_id,
        market_id=market.market_id,
        question=market.question or "",
        event_title=market.event_title,
        market_type=cl.market_type,
        side=side,
        market_implied_prob=round(implied_prob, 4) if implied_prob is not None else None,
        model_estimated_prob=m2r.estimated_prob,
        probability_gap_pp=m2r.gap_pp,
        confidence_score=confidence,
        module1_result=cl.market_type,
        module2_result=m2r.data_quality,
        module4_result="confirmed" if m4r.confirmed else "not_confirmed",
        module5_result="pass",
        liquidity_ok=True,
        weather_data_fresh=(m2r.data_quality != "insufficient"),
        settlement_source_verified=m2r.settlement_verified,
        recommendation=rec,
        explanation=explanation[:2000],
        created_at=now,
    )


def run_signal_evaluation() -> SignalRun:
    """
    Evaluate all active markets. Store signals and run record.
    Returns the SignalRun log. NEVER raises.

    This function generates ANALYTICAL SIGNALS ONLY.
    No trades, no paper trades, no portfolio updates.
    """
    t_start = time.monotonic()
    run = SignalRun(run_at=_now_iso(), status="running")

    # Commit run record first to get run_id
    with Session(engine, expire_on_commit=False) as s:
        s.add(run)
        s.commit()
        run_id = run.id

    counters: dict[str, int] = {}
    total = 0
    errors = 0

    try:
        # Load active, non-closed markets
        with Session(engine) as s:
            markets = s.exec(
                select(Market)
                .where(Market.is_closed == False)   # noqa: E712
                .limit(MAX_MARKETS_PER_RUN)
            ).all()

        logger.info("Signal engine: evaluating %d markets", len(markets))

        # Evaluate each market
        signals: list[Signal] = []
        for market in markets:
            try:
                sig = evaluate_market(market, run_id)
                signals.append(sig)
                rec = sig.recommendation
                counters[rec] = counters.get(rec, 0) + 1
                total += 1
            except Exception as e:
                logger.warning("Signal eval error for market %s: %s", market.market_id, e)
                errors += 1

        # Bulk insert signals
        with Session(engine, expire_on_commit=False) as s:
            for sig in signals:
                s.add(sig)
            s.commit()
        logger.info("Signal engine: stored %d signals", len(signals))

    except Exception as e:
        logger.error("Signal engine fatal error: %s", e)
        errors += 1

    duration_ms = int((time.monotonic() - t_start) * 1000)

    enter_count = counters.get("ENTER_CANDIDATE", 0) + counters.get("NEEDS_SETTLEMENT_SOURCE_CHECK", 0)
    watch_count = counters.get("WATCH", 0) + counters.get("NEEDS_MORE_DATA", 0)
    skip_count = sum(v for k, v in counters.items() if k.startswith("SKIP"))

    # Update run record
    with Session(engine, expire_on_commit=False) as s:
        run_rec = s.exec(select(SignalRun).where(SignalRun.id == run_id)).first()
        if run_rec:
            run_rec.status = "error" if errors > total else "ok"
            run_rec.markets_evaluated = total
            run_rec.enter_candidates = enter_count
            run_rec.watch_count = watch_count
            run_rec.skip_count = skip_count
            run_rec.duration_ms = duration_ms
            run_rec.recommendation_counts = json.dumps(counters)
            run_rec.errors = errors
            s.add(run_rec)
            s.commit()
            return run_rec

    run.status = "ok"
    run.markets_evaluated = total
    run.enter_candidates = enter_count
    run.watch_count = watch_count
    run.skip_count = skip_count
    run.duration_ms = duration_ms
    return run
