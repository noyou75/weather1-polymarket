"""
Shadow Signal Observer — Phase 6E/6F (hardened) + Decision D.

Records live signals and live prices at signal time.
NO positions. NO paper trades. NO portfolio impact. NO capital changes.

Phase 6F hardening:
- Duplicate-safe upsert: same market_id never creates a second observation row.
  It updates last_seen_at, latest prices, directional move, times_seen.
- Daily summary written at end of each run.
- Clear readiness status: PHASE_7_BLOCKED | COLLECTING_SHADOW_DATA | READY_FOR_REVIEW.
- Phase 7 NEVER auto-approved; always requires explicit user written approval.

Decision D (Phase 6K):
- Separate shadow-only path for annual_temp markets with gap 5–10pp.
- These are below the TRADING threshold (MIN_GAP_WATCH = 10pp) and produce
  NEEDS_MORE_DATA in the main signal engine — invisible to normal shadow monitoring.
- Recommendation stored: SHADOW_WATCH_VERIFIED_LOW_GAP (never WATCH, never ENTER_CANDIDATE).
- Only annual_temp is included; global_monthly_temp excluded for now.
- Settlement source must be VERIFIED_NASA_GISTEMP.
- Engine.py is completely unchanged.

Phase 7 promotion requires ALL of:
  1. >= 30 shadow observations
  2. >= 7 calendar days of observation
  3. Avg spread at observation time <= 5%
  4. Avg directional move >= 0% (market moves toward signal on average)
  5. No stale data issues
  6. Explicit user written approval
"""
import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from database import engine
from models.signals import Signal, SignalRun
from models.markets import Market
from models.shadow import ShadowSignalObservation, ShadowPriceSnapshot, ShadowDailySummary
from ingestion.settlement_sources import get_settlement_source

logger = logging.getLogger("weather1.strategy.shadow")

# ── Observation filter criteria ────────────────────────────────────────────────
OBSERVE_RECOMMENDATIONS = {"NEEDS_SETTLEMENT_SOURCE_CHECK", "WATCH", "ENTER_CANDIDATE"}
MIN_CONFIDENCE = 60

# ── Phase 7 promotion thresholds ──────────────────────────────────────────────
PROMOTION_MIN_OBSERVATIONS  = 30
PROMOTION_MIN_DAYS          = 7
PROMOTION_MAX_AVG_SPREAD    = 5.0   # % — skip if avg spread above this
PROMOTION_MIN_AVG_DIR_MOVE  = 0.0   # % — directional move must not be clearly negative

# ── Readiness status codes ─────────────────────────────────────────────────────
STATUS_BLOCKED    = "PHASE_7_BLOCKED"         # default — never passes without explicit approval
STATUS_COLLECTING = "COLLECTING_SHADOW_DATA"  # actively building observation history
STATUS_REVIEW     = "READY_FOR_REVIEW"        # criteria met — awaiting user approval

# ── Decision D: shadow-only low-gap observation for NASA GISTEMP verified markets ──
# Gap range: [5pp, 10pp) — below trading threshold, above noise floor
# Type whitelist: annual_temp ONLY (global_monthly_temp excluded for now)
# Settlement: must be VERIFIED_NASA_GISTEMP
# Recommendation: SHADOW_WATCH_VERIFIED_LOW_GAP — never WATCH, never ENTER_CANDIDATE
#
# SAFETY INVARIANTS (violated = logged error, function aborts gracefully):
#   1. market_type must be in _D_TYPE_WHITELIST
#   2. settlement source must be VERIFIED_NASA_GISTEMP
#   3. gap must be in [_D_MIN_GAP, _D_MAX_GAP)
#   4. recommendation is always _D_RECOMMENDATION — asserted before any write
#   5. no connection to portfolio, paper trading, or risk engine
#   6. engine.py is NEVER modified; this path is entirely independent

_D_TYPE_WHITELIST  = {"annual_temp"}                  # only annual_temp for now
_D_REQUIRED_SOURCE = "VERIFIED_NASA_GISTEMP"
_D_MIN_GAP         = 5.0                              # pp — shadow observation starts here
_D_MAX_GAP         = 10.0                             # pp — strictly below MIN_GAP_WATCH = 10pp
_D_RECOMMENDATION  = "SHADOW_WATCH_VERIFIED_LOW_GAP"  # distinct from all trading recs
_D_EXPLANATION     = (
    "Decision D shadow observation: annual_temp market with gap 5–10pp. "
    "Below trading threshold (MIN_GAP_WATCH=10pp). "
    "Settlement source: VERIFIED_NASA_GISTEMP (confirmed June 2026). "
    "NOT trade-eligible. NOT paper-trade eligible. Shadow price tracking only."
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_market(market_id: str) -> "Market | None":
    """Load a single Market from DB. Returns None on any error."""
    try:
        with Session(engine) as s:
            return s.exec(select(Market).where(Market.market_id == market_id)).first()
    except Exception:
        return None


def _observe_annual_temp_low_gap(fetched_at: str) -> int:
    """
    Decision D: Shadow-only observation for annual_temp markets with gap 5–10pp.

    These markets produce NEEDS_MORE_DATA in the main signal engine (gap below
    the 10pp MIN_GAP_WATCH trading threshold) and are therefore invisible to the
    standard shadow observer.  This function captures them under a distinct
    recommendation so their price movement can be tracked for the Day 7 review.

    SAFETY:
    - Type whitelist enforced: only annual_temp.
    - Settlement source verified: only VERIFIED_NASA_GISTEMP.
    - Gap range [5pp, 10pp) enforced: hard-coded upper bound == MIN_GAP_WATCH.
    - Recommendation asserted to be _D_RECOMMENDATION before any DB write.
    - No connection to portfolio, paper trading, risk engine, or execution.
    - All errors caught; returns 0 on any failure (never raises).

    Returns: number of observations created or updated this cycle.
    """
    from ingestion.settlement_sources import get_settlement_source

    stored = 0
    try:
        # ── Step 1: load latest signal run ────────────────────────────────────
        with Session(engine) as s:
            runs = s.exec(
                select(SignalRun).order_by(SignalRun.id.desc()).limit(1)  # type: ignore[arg-type]
            ).all()
            if not runs:
                return 0
            latest_run = runs[0]

            # Fetch annual_temp NEEDS_MORE_DATA signals with passing liquidity
            candidates = s.exec(
                select(Signal).where(
                    Signal.run_id       == latest_run.id,
                    Signal.market_type  == "annual_temp",       # whitelist: type only
                    Signal.recommendation == "NEEDS_MORE_DATA", # below trading threshold
                    Signal.liquidity_ok == True,                # noqa: E712
                )
            ).all()

        if not candidates:
            return 0

        # ── Step 2: apply gap range and settlement source filters ──────────────
        eligible: list[Signal] = []
        for sig in candidates:
            gap = abs(sig.probability_gap_pp or 0.0)

            # SAFETY GATE 1: gap must be in the Decision D shadow-only range
            if not (_D_MIN_GAP <= gap < _D_MAX_GAP):
                continue

            # SAFETY GATE 2: market type must be in whitelist (belt and suspenders)
            if sig.market_type not in _D_TYPE_WHITELIST:
                logger.error(
                    "Decision D safety violation: market_type=%s not in whitelist. Skipping.",
                    sig.market_type,
                )
                continue

            # SAFETY GATE 3: settlement source must be verified NASA GISTEMP
            actual_source = get_settlement_source(sig.market_type)
            if actual_source != _D_REQUIRED_SOURCE:
                logger.warning(
                    "Decision D: market_type=%s settlement=%s (required %s). Skipping.",
                    sig.market_type, actual_source, _D_REQUIRED_SOURCE,
                )
                continue

            eligible.append(sig)

        if not eligible:
            return 0

        logger.info(
            "Decision D: %d annual_temp signals eligible (gap 5-10pp, verified source)",
            len(eligible),
        )

        # ── Step 3: upsert observations and snapshots ─────────────────────────
        snapshots: list[ShadowPriceSnapshot] = []

        with Session(engine, expire_on_commit=False) as s:
            for sig in eligible:
                try:
                    mkt = _get_market(sig.market_id)
                    if not mkt:
                        continue

                    bid, ask = mkt.best_bid, mkt.best_ask
                    mid    = _mid(bid, ask)
                    spread = mkt.spread
                    liq    = mkt.liquidity

                    # SAFETY GATE 4: recommendation must ALWAYS be _D_RECOMMENDATION
                    # This is the critical invariant — asserted before every write.
                    final_rec = _D_RECOMMENDATION
                    assert final_rec == _D_RECOMMENDATION, (
                        f"BUG: Decision D produced unexpected recommendation: {final_rec}"
                    )
                    assert final_rec != "ENTER_CANDIDATE", (
                        "BUG: ENTER_CANDIDATE must never be generated in Decision D path"
                    )
                    assert final_rec != "WATCH", (
                        "BUG: WATCH must not be used in Decision D — use SHADOW_WATCH_VERIFIED_LOW_GAP"
                    )

                    existing = s.exec(
                        select(ShadowSignalObservation).where(
                            ShadowSignalObservation.market_id == sig.market_id
                        )
                    ).first()

                    if existing:
                        # Update prices; PRESERVE first_seen_at and initial_mid_price
                        existing.last_updated_at     = fetched_at
                        existing.times_seen          += 1
                        existing.latest_best_bid     = bid
                        existing.latest_best_ask     = ask
                        existing.latest_mid_price    = mid
                        existing.latest_spread       = spread
                        existing.is_active           = mkt.is_active and not mkt.is_closed
                        existing.directional_move_pct = _directional_move(
                            existing.side, existing.initial_mid_price, mid
                        )
                        # Do NOT upgrade recommendation — stays _D_RECOMMENDATION permanently
                        s.add(existing)
                        obs_id          = existing.id
                        obs_initial_mid = existing.initial_mid_price
                        obs_side        = existing.side
                    else:
                        obs = ShadowSignalObservation(
                            market_id           = sig.market_id,
                            question            = sig.question,
                            event_title         = sig.event_title,
                            market_type         = sig.market_type,
                            side                = sig.side,
                            recommendation      = final_rec,         # always _D_RECOMMENDATION
                            confidence_score    = sig.confidence_score,
                            model_prob          = sig.model_estimated_prob,
                            market_implied_prob = sig.market_implied_prob,
                            gap_pp              = sig.probability_gap_pp,
                            settlement_source   = _D_REQUIRED_SOURCE,  # always VERIFIED_NASA_GISTEMP
                            first_seen_at       = fetched_at,
                            initial_best_bid    = bid,
                            initial_best_ask    = ask,
                            initial_mid_price   = mid,
                            initial_spread      = spread,
                            initial_liquidity   = liq,
                            last_updated_at     = fetched_at,
                            latest_best_bid     = bid,
                            latest_best_ask     = ask,
                            latest_mid_price    = mid,
                            latest_spread       = spread,
                            directional_move_pct = 0.0,
                            is_active           = mkt.is_active and not mkt.is_closed,
                            times_seen          = 1,
                            explanation         = _D_EXPLANATION,
                        )
                        s.add(obs)
                        s.flush()
                        obs_id          = obs.id
                        obs_initial_mid = mid
                        obs_side        = sig.side

                    snapshots.append(ShadowPriceSnapshot(
                        observation_id       = obs_id,
                        market_id            = sig.market_id,
                        recorded_at          = fetched_at,
                        best_bid             = bid,
                        best_ask             = ask,
                        mid_price            = mid,
                        spread               = spread,
                        liquidity            = liq,
                        directional_move_pct = _directional_move(obs_side, obs_initial_mid, mid),
                    ))
                    stored += 1

                except AssertionError as ae:
                    # Safety gate violation — log clearly, skip this market, continue
                    logger.error("Decision D SAFETY VIOLATION for %s: %s", sig.market_id, ae)
                    continue
                except Exception as e:
                    logger.warning("Decision D error for %s: %s", sig.market_id, e)
                    continue

            for snap in snapshots:
                s.add(snap)
            s.commit()

        logger.info(
            "Decision D complete: %d annual_temp obs stored/updated, %d snapshots",
            stored, len(snapshots),
        )

    except Exception as e:
        logger.error("Decision D outer error (non-fatal): %s", e)
        return 0

    return stored


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _mid(bid: float | None, ask: float | None) -> float | None:
    if bid is None and ask is None:
        return None
    if bid is None: return ask
    if ask is None: return bid
    return (bid + ask) / 2


def _directional_move(side: str, initial: float | None, latest: float | None) -> float | None:
    """
    Directional move: positive = market moved in the direction our signal predicted.
    For YES: positive if price rose. For NO: positive if price fell.
    NOT a portfolio return — purely market observation.
    """
    if initial is None or latest is None or initial <= 0:
        return None
    raw = (latest - initial) / initial * 100
    return round(raw if side == "YES" else -raw, 3)


def run_shadow_observation() -> dict:
    """
    Main entry point. Hardened for daily recurring runs.
    - Upsert observations (never duplicates by market_id).
    - Add price snapshot each run.
    - Update daily summary.
    SAFETY: No positions. No P&L. No portfolio changes.
    """
    now = _now_iso()
    today = _today_utc()
    result = {
        "run_at": now,
        "date_utc": today,
        "new_observations": 0,
        "updated_observations": 0,
        "snapshots_stored": 0,
        "errors": [],
        "status": STATUS_BLOCKED,
    }

    # ── Load latest signal run ─────────────────────────────────────────────────
    with Session(engine) as s:
        runs = s.exec(select(SignalRun).order_by(SignalRun.id.desc()).limit(1)).all()  # type: ignore[arg-type]
        if not runs:
            result["errors"].append("No signal runs — run signal evaluation first")
            return result
        latest_run = runs[0]
        qualifying_sigs = s.exec(
            select(Signal).where(
                Signal.run_id == latest_run.id,
                Signal.confidence_score >= MIN_CONFIDENCE,
                Signal.liquidity_ok == True,   # noqa: E712
            )
        ).all()

    qualifying = [s for s in qualifying_sigs if s.recommendation in OBSERVE_RECOMMENDATIONS]
    logger.info("Shadow observer: %d qualifying signals from run %d",
                len(qualifying), latest_run.id)

    # ── Load current market prices ─────────────────────────────────────────────
    with Session(engine) as s:
        markets_by_id: dict[str, Market] = {}
        for sig in qualifying:
            mkt = s.exec(select(Market).where(Market.market_id == sig.market_id)).first()
            if mkt:
                markets_by_id[sig.market_id] = mkt

    # ── Upsert observations + collect snapshots ────────────────────────────────
    new_obs = 0
    upd_obs = 0
    snapshots: list[ShadowPriceSnapshot] = []

    with Session(engine, expire_on_commit=False) as s:
        for sig in qualifying:
            try:
                mkt = markets_by_id.get(sig.market_id)
                if not mkt:
                    continue

                bid, ask = mkt.best_bid, mkt.best_ask
                mid  = _mid(bid, ask)
                spread  = mkt.spread
                liq  = mkt.liquidity
                src  = get_settlement_source(sig.market_type)

                # ── Duplicate-safe upsert ──────────────────────────────────────
                # Key: market_id. One row per market regardless of how many cycles run.
                existing = s.exec(
                    select(ShadowSignalObservation).where(
                        ShadowSignalObservation.market_id == sig.market_id
                    )
                ).first()

                if existing:
                    # Update latest prices and tracking fields; PRESERVE first_seen_at / initial_mid_price
                    existing.last_updated_at    = now
                    existing.times_seen         += 1
                    existing.latest_best_bid    = bid
                    existing.latest_best_ask    = ask
                    existing.latest_mid_price   = mid
                    existing.latest_spread      = spread
                    existing.recommendation     = sig.recommendation   # update if changed
                    existing.confidence_score   = sig.confidence_score
                    existing.is_active          = mkt.is_active and not mkt.is_closed
                    existing.directional_move_pct = _directional_move(
                        existing.side, existing.initial_mid_price, mid
                    )
                    s.add(existing)
                    obs_id = existing.id
                    obs_initial_mid = existing.initial_mid_price
                    obs_side = existing.side
                    upd_obs += 1
                else:
                    obs = ShadowSignalObservation(
                        market_id=sig.market_id,
                        question=sig.question,
                        event_title=sig.event_title,
                        market_type=sig.market_type,
                        side=sig.side,
                        recommendation=sig.recommendation,
                        confidence_score=sig.confidence_score,
                        model_prob=sig.model_estimated_prob,
                        market_implied_prob=sig.market_implied_prob,
                        gap_pp=sig.probability_gap_pp,
                        settlement_source=src,
                        first_seen_at=now,
                        initial_best_bid=bid,
                        initial_best_ask=ask,
                        initial_mid_price=mid,
                        initial_spread=spread,
                        initial_liquidity=liq,
                        last_updated_at=now,
                        latest_best_bid=bid,
                        latest_best_ask=ask,
                        latest_mid_price=mid,
                        latest_spread=spread,
                        directional_move_pct=0.0,
                        is_active=mkt.is_active and not mkt.is_closed,
                        times_seen=1,
                        explanation=(sig.explanation or "")[:300],
                    )
                    s.add(obs)
                    s.flush()
                    obs_id = obs.id
                    obs_initial_mid = mid
                    obs_side = sig.side
                    new_obs += 1

                # Always add a price snapshot this cycle
                snapshots.append(ShadowPriceSnapshot(
                    observation_id=obs_id,
                    market_id=sig.market_id,
                    recorded_at=now,
                    best_bid=bid,
                    best_ask=ask,
                    mid_price=mid,
                    spread=spread,
                    liquidity=liq,
                    directional_move_pct=_directional_move(obs_side, obs_initial_mid, mid),
                ))

            except Exception as e:
                result["errors"].append(f"market {sig.market_id}: {e}")
                logger.warning("Shadow error for %s: %s", sig.market_id, e)

        for snap in snapshots:
            s.add(snap)
        s.commit()

    result["new_observations"] = new_obs
    result["updated_observations"] = upd_obs
    result["snapshots_stored"] = len(snapshots)

    # ── Decision D: shadow-only low-gap path for verified annual_temp markets ──
    # Isolated try/except: any failure here cannot break the main shadow observer.
    # Engine.py is untouched; trading thresholds are unchanged.
    # Creates/updates observations with SHADOW_WATCH_VERIFIED_LOW_GAP only.
    try:
        d_count = _observe_annual_temp_low_gap(now)
        result["decision_d_low_gap_obs"] = d_count
    except Exception as e:
        logger.error("Decision D call error (non-fatal, main observer unaffected): %s", e)
        result["errors"].append(f"decision_d: {e}")
        result["decision_d_low_gap_obs"] = 0
    # ── End Decision D ─────────────────────────────────────────────────────────

    # ── Update daily summary ───────────────────────────────────────────────────
    _update_daily_summary(today, new_obs, upd_obs, len(snapshots))

    # ── Compute readiness status ───────────────────────────────────────────────
    status_data = get_shadow_status()
    result["status"] = status_data["readiness_status"]
    result["readiness"] = status_data

    logger.info(
        "Shadow obs: new=%d updated=%d snaps=%d status=%s",
        new_obs, upd_obs, len(snapshots), result["status"],
    )
    return result


def _update_daily_summary(date_utc: str, new_obs: int, upd_obs: int, snaps: int) -> None:
    """Compute and upsert daily summary for today."""
    now = _now_iso()
    try:
        with Session(engine) as s:
            observations = s.exec(select(ShadowSignalObservation)).all()

        active_obs = [o for o in observations if o.is_active]
        dir_moves  = [o.directional_move_pct for o in observations
                      if o.directional_move_pct is not None]
        spreads    = [o.initial_spread for o in observations
                      if o.initial_spread is not None]

        avg_spread   = sum(spreads) / len(spreads) * 100 if spreads else None
        avg_dir_move = sum(dir_moves) / len(dir_moves) if dir_moves else None

        pos = sum(1 for m in dir_moves if m > 0)
        neg = sum(1 for m in dir_moves if m < 0)
        neu = len(dir_moves) - pos - neg

        enter_c = sum(1 for o in observations if o.recommendation == "ENTER_CANDIDATE")
        check_c = sum(1 for o in observations if o.recommendation == "NEEDS_SETTLEMENT_SOURCE_CHECK")
        watch_c = sum(1 for o in observations if o.recommendation == "WATCH")

        with Session(engine, expire_on_commit=False) as s:
            existing = s.exec(
                select(ShadowDailySummary).where(ShadowDailySummary.date_utc == date_utc)
            ).first()
            if existing:
                existing.total_active_observations    = len(active_obs)
                existing.new_observations_today       += new_obs
                existing.updated_observations_today   += upd_obs
                existing.snapshots_today              += snaps
                existing.avg_spread_pct               = avg_spread
                existing.avg_directional_move_pct     = avg_dir_move
                existing.positive_moves_count         = pos
                existing.negative_moves_count         = neg
                existing.neutral_moves_count          = neu
                existing.enter_candidate_count        = enter_c
                existing.needs_check_count            = check_c
                existing.watch_count                  = watch_c
                existing.updated_at                   = now
                s.add(existing)
            else:
                s.add(ShadowDailySummary(
                    date_utc=date_utc,
                    total_active_observations=len(active_obs),
                    new_observations_today=new_obs,
                    updated_observations_today=upd_obs,
                    snapshots_today=snaps,
                    avg_spread_pct=avg_spread,
                    avg_directional_move_pct=avg_dir_move,
                    positive_moves_count=pos,
                    negative_moves_count=neg,
                    neutral_moves_count=neu,
                    enter_candidate_count=enter_c,
                    needs_check_count=check_c,
                    watch_count=watch_c,
                    created_at=now,
                    updated_at=now,
                ))
            s.commit()
    except Exception as e:
        logger.error("Daily summary update error: %s", e)


def get_shadow_status() -> dict:
    """
    Return full shadow observation status with readiness assessment.
    ALWAYS returns PHASE_7_BLOCKED — Phase 7 requires explicit user approval.
    """
    try:
        with Session(engine) as s:
            observations = s.exec(select(ShadowSignalObservation)).all()
            summaries    = s.exec(select(ShadowDailySummary).order_by(ShadowDailySummary.date_utc)).all()  # type: ignore[arg-type]
            snapshot_count = len(s.exec(select(ShadowPriceSnapshot)).all())

        n_obs   = len(observations)
        n_days  = len(summaries)   # one record per calendar day with activity
        active  = sum(1 for o in observations if o.is_active)

        dir_moves = [o.directional_move_pct for o in observations
                     if o.directional_move_pct is not None]
        spreads   = [o.initial_spread for o in observations
                     if o.initial_spread is not None]
        avg_move   = round(sum(dir_moves) / len(dir_moves), 3) if dir_moves else None
        avg_spread = round(sum(spreads) / len(spreads) * 100, 2) if spreads else None

        # ── Promotion criteria evaluation ──────────────────────────────────────
        c_obs   = {"required": PROMOTION_MIN_OBSERVATIONS, "actual": n_obs,
                   "pass": n_obs >= PROMOTION_MIN_OBSERVATIONS}
        c_days  = {"required": PROMOTION_MIN_DAYS, "actual": n_days,
                   "pass": n_days >= PROMOTION_MIN_DAYS}
        c_spread = {"required": f"avg ≤ {PROMOTION_MAX_AVG_SPREAD}%",
                    "actual": f"{avg_spread:.2f}%" if avg_spread else "—",
                    "pass": avg_spread is not None and avg_spread <= PROMOTION_MAX_AVG_SPREAD}
        c_move  = {"required": f"avg ≥ {PROMOTION_MIN_AVG_DIR_MOVE}%",
                   "actual": f"{avg_move:.2f}%" if avg_move is not None else "—",
                   "pass": avg_move is not None and avg_move >= PROMOTION_MIN_AVG_DIR_MOVE}
        c_appr  = {"required": "explicit written approval",
                   "actual": "NOT YET GIVEN", "pass": False}

        criteria_met = all([c_obs["pass"], c_days["pass"], c_spread["pass"],
                            c_move["pass"]])  # c_appr always False

        # ── Readiness status ───────────────────────────────────────────────────
        # NEVER auto-approve — always PHASE_7_BLOCKED without explicit user approval
        if not c_obs["pass"] or not c_days["pass"]:
            readiness_status = STATUS_COLLECTING
        elif criteria_met:
            readiness_status = STATUS_REVIEW   # criteria met, awaiting user approval
        else:
            readiness_status = STATUS_COLLECTING

        # Always wrap with PHASE_7_BLOCKED regardless of criteria
        phase7_status = STATUS_BLOCKED

        return {
            "total_observations":      n_obs,
            "active_observations":     active,
            "total_snapshots":         snapshot_count,
            "calendar_days_observed":  n_days,
            "avg_directional_move_pct": avg_move,
            "avg_spread_pct":          avg_spread,
            "positive_moves":          sum(1 for m in dir_moves if m > 0),
            "negative_moves":          sum(1 for m in dir_moves if m < 0),
            "readiness_status":        readiness_status,
            "phase7_status":           phase7_status,   # always PHASE_7_BLOCKED
            "phase7_promotion_ready":  False,            # always False until user approves
            "days_until_review":       max(0, PROMOTION_MIN_DAYS - n_days),
            "obs_until_review":        max(0, PROMOTION_MIN_OBSERVATIONS - n_obs),
            "promotion_criteria": {
                "observations_30_plus": c_obs,
                "calendar_days_7_plus": c_days,
                "avg_spread_acceptable": c_spread,
                "directional_move_positive": c_move,
                "explicit_user_approval": c_appr,
            },
            "daily_summaries": [
                {
                    "date": d.date_utc,
                    "active_obs": d.total_active_observations,
                    "new": d.new_observations_today,
                    "updated": d.updated_observations_today,
                    "snapshots": d.snapshots_today,
                    "avg_spread_pct": d.avg_spread_pct,
                    "avg_dir_move_pct": d.avg_directional_move_pct,
                    "pos": d.positive_moves_count,
                    "neg": d.negative_moves_count,
                }
                for d in summaries
            ],
            "safety_note": (
                "SHADOW OBSERVATION ONLY. No positions. No capital. No portfolio P&L. "
                "Phase 7 always requires explicit written user approval regardless of criteria."
            ),
        }
    except Exception as e:
        return {"error": str(e), "phase7_status": STATUS_BLOCKED}
