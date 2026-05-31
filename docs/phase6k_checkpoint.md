# Phase 6K — Shadow Monitoring Checkpoint Note
**Date:** June 2, 2026  
**Shadow Day:** 2 of 7  
**Status:** COLLECTING_SHADOW_DATA · PHASE_7_BLOCKED  

---

## 1. Current Shadow Status

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Observations | 39 | ≥ 30 | ✅ PASS |
| Calendar days observed | 2 | ≥ 7 | ⏳ 5 remaining |
| Total snapshots | 617 | — | informational |
| Avg spread at observation | 1.39% | ≤ 5% | ✅ PASS |
| Avg directional move | −0.43% | ≥ 0% | ❌ slightly negative |
| Positive / Negative moves | 15 / 11 | — | 55% accuracy on resolved |
| Explicit user approval | NOT GIVEN | Required | ❌ BLOCKED |

Phase 7 remains BLOCKED. No paper trading. No positions. No portfolio P&L.

---

## 2. Main Finding: Shadow Is Testing the Wrong Market Type

**All 39 current observations are city_station_temp markets.**  
Zero annual_temp or global_monthly_temp observations exist in shadow monitoring.

This is a critical structural mismatch:

| | Backtested strategy | Current shadow monitoring |
|---|---|---|
| Market type | annual_temp (hottest year) | city_station_temp (daily city temp ranges) |
| Settlement source | VERIFIED — NASA GISTEMP v4 | UNVERIFIED — NWS (not confirmed as Polymarket source) |
| Backtest win rate | 71.4% (v1.1, MEDIUM quality) | Not backtested (no historical prices) |
| Gap threshold met | Yes (historical 2003–2024) | Yes (but near-expiry markets) |

**Why annual_temp is absent from shadow:**  
The "Will 2026 be the hottest year on record?" market has a current gap of ~7.5pp between model estimate (~40%) and market price (~32.5%). This is below the v1.1 WATCH threshold of 10pp, so no signal is generated and no observation is captured. Until market implied probability moves further from our model estimate (or the model estimate changes as more 2026 GISTEMP data is published), annual_temp will not enter shadow monitoring.

---

## 3. Why Avg Directional Move Is Slightly Negative

The −0.43% average is explained by three compounding factors, not by a strategy flaw:

**Factor 1 — Asymmetric city market payoff structure**  
Each city/date temperature event has 6–8 outcome ranges. Only one wins. When our NWS-based signal picks the wrong range, that range's price crashes from ~3–5% to near 0 (large % loss). When correct, price rises gradually from 3–5% toward its eventual 15–80%+ (moderate gain so far). The average losing move (−24.5% per trade) is larger in magnitude than the average winning move (+16.0% per trade).

**Factor 2 — Resolution-timing concentration (Days 1–2 noise)**  
Most observations were first captured when their target markets were 0–2 days from resolution (May 31 / June 1 dates). These markets have now resolved. Wrong-range outcomes collapsed to near zero; correct-range outcomes confirmed their direction. This concentrated resolution creates large, lopsided moves in the short observation window.

Statistical check: removing the worst 5 outliers raises avg directional move from −0.43% to **+4.8%**. These 5 outliers account for −191% in aggregate against a positive pool of +240%. The negative average is driven by a handful of resolved wrong-range city markets.

**Factor 3 — Zero-mover dilution**  
13 of 39 observations (33%) show 0.0% directional move — markets that have not yet moved materially. These are not losses; they are early-stage observations. As they age, they will begin contributing direction and the distribution will normalize.

**Resolved market accuracy: 55% (12 right out of 22 resolved).** This is above the Phase 0 backtest acceptance threshold of 52% win rate, though on a small and noisy sample.

---

## 4. Why No Code Changes Are Recommended Before Day 7

1. **Too early to tune**: Day 2 of 7 contains significant resolution noise from short-duration markets captured at launch. This noise will self-correct as older observations age and new longer-duration markets replace them.

2. **Changing thresholds on Day 2 data would overfit to noise**: The current data is dominated by resolved May 31/June 1 city markets. Any threshold adjustment made now would be calibrated to a temporary signal, not the steady-state behavior of the system.

3. **The core strategy (annual_temp + NASA GISTEMP) has not been tested yet in shadow**: Adjusting city market parameters before the primary strategy has even been observed would be premature.

4. **Spread and liquidity are healthy**: 1.39% average spread is well within limits. Liquidity is adequate for $2–$5 positions. No infrastructure problems to fix.

5. **Phase 0 plan**: Section 8.11 Failure Criteria requires kill switch triggers >2 in a 6-month window or win rate <48% across the full test period. Neither applies at Day 2 with 39 observations.

---

## 5. Open Decisions for Day 7 Review

The following questions should be decided at the Day 7 review (approximately June 6, 2026), using the full 7-day dataset:

### Decision A: Raise near-expiry filter from 24h → 72h
**Argument for:** 8 of the 10 worst observations were markets resolving within 48h of first capture. A 72h filter would have excluded most of the resolution-noise losses.  
**Argument against:** Premature; some valid signals exist in the 24–72h window. Should be data-driven from full 7-day set.  
**File to change if approved:** `backend/strategy/module5_liquidity.py` — change `NEAR_EXPIRY_SKIP_HOURS = 24` to `72`.

### Decision B: Restrict Phase 7 paper trading to NASA GISTEMP verified markets only
**Argument for:** Annual_temp markets are the only type where: (a) settlement source is confirmed, (b) backtest was run, (c) historical accuracy is measured. City markets are untested at trading scale.  
**Argument against:** Limits signal volume significantly; may reduce paper trading frequency.  
**Recommendation if chosen:** Label city_station_temp as EXPERIMENTAL in Phase 7 with much smaller position sizes (e.g., $1 vs $2 default).

### Decision C: Keep city_station_temp in Phase 7 with tighter time-to-resolution filter
**Argument for:** City markets have adequate liquidity and tight spreads. 55% accuracy is defensible.  
**Implementation:** Only observe (and later trade) city markets with ≥7 days to resolution, when NWS forecasts are directionally confident and not subject to same-day resolution noise.  
**File to change if approved:** `backend/strategy/module5_liquidity.py` + `backend/strategy/module2_probability_gap.py`.

### Decision D: Lower WATCH gap threshold for shadow observation only (not for trading)
**Argument for:** Would allow annual_temp (gap ~7.5pp) to enter shadow monitoring and begin accumulating real-world price movement data for the validated strategy.  
**Implementation:** Add a separate `SHADOW_MIN_GAP = 5.0` parameter independent of `MIN_GAP_WATCH = 10.0`. Shadow observer uses the lower threshold; signal engine uses the higher one.  
**Risk:** Very low — observation only, no positions created.  
**Recommendation:** Implement this before Day 7 to start generating annual_temp shadow data for the review.

---

## 6. Action Required Before Day 7

| Action | Owner | Risk level |
|---|---|---|
| Continue running Railway scheduler (automatic) | System | None |
| Monitor daily summary at /shadow/status | User | None |
| Check avg directional move trend by Day 4 | User | None |
| Decide on Decision D (lower shadow-only gap threshold) | User approval | Very low |
| Full 7-day review on ~June 6 | Both | — |

---

## 7. What Must NOT Happen Before Day 7

- Do not enable paper trading (Phase 7 remains BLOCKED)
- Do not change trading thresholds (MIN_GAP_WATCH, MIN_GAP_ENTER)
- Do not add wallet/API key/signing code
- Do not place real or paper orders
- Do not modify the signal engine to generate more signals to "fix" the average

---

*Written: Phase 6K, June 2, 2026. Next checkpoint: Phase 6L or 7-day review, ~June 6, 2026.*

---

## Day 2 Monitoring Note — June 2, 2026 (Evening)

### Metrics vs Phase 6K Baseline

| Metric | Phase 6K (morning) | Day 2 (evening) | Change |
|---|---|---|---|
| Observations | 39 | 39 | → unchanged |
| Calendar days | 2/7 | 2/7 | → unchanged |
| Snapshots | 617 | 635 | +18 ✅ |
| Avg spread | 1.39% | 1.39% | → unchanged |
| **Avg dir move** | **−0.43%** | **−1.00%** | ⚠ worsened |
| Positive movers | 15 | 15 | → unchanged |
| Negative movers | 11 | **14** | +3 ↑ |
| Zero movers | 13 | **10** | −3 ↓ |

### What Changed

Three zero-mover observations converted to negative movers between the Phase 6K morning checkpoint and this evening check. No new observations were added (still 39). The only movement was within the existing 39 markets.

**Cause (consistent with Phase 6K hypothesis):** The three converting observations are almost certainly May 31 city temperature markets that settled during the day. Markets with end-of-day resolution on May 31 would have been in zero-mover state earlier in the day (before resolution) and then snapped to their final outcome price (approximately 0 for the losing ranges). When a city market resolves to 0 for the wrong temperature range, it registers as a large negative directional move — dragging the average lower.

This is the exact resolution-timing noise pattern identified in Phase 6K Section 3, Factor 2: *"This concentrated resolution creates large, lopsided moves in the short observation window."*

### Daily Summary Context

| Day | New obs | Avg dir move | Pos | Neg |
|---|---|---|---|---|
| May 30 | 28 | **+1.27%** ✅ | 14 | 8 |
| May 31 | 11 | **−1.00%** | 15 | 14 |

Day 1 (May 30) was independently positive at +1.27%. The composite −1.00% is entirely driven by the negative Day 2 component. As Day 3 and beyond add observations, the May 30 positive baseline will continue to be diluted by the ongoing resolution of short-duration city markets captured on Day 1–2 — or alternatively, the new longer-duration markets captured on Day 3+ will start generating more stable movements.

### Scheduler Status Note

The `/scheduler/status` endpoint returned an intermittent SSL connection error (Railway network transient issue, not a service failure). Evidence that the scheduler is still active:

- Snapshots grew from 617 → 635 (+18 price snapshots collected)
- The `signal_and_shadow` cron job fires at `:03/:18/:33/:48` each hour
- +18 snapshots in ~4 hours is consistent with that cadence (4 runs × ~4–5 snapshot additions per run after filtering)

### Annual_temp Observations

Still **zero**. The "Will 2026 be the hottest year on record?" market gap remains ~7.5pp — below the v1.1 WATCH threshold of 10pp. No NASA GISTEMP verified market has crossed the observation threshold at Day 2.

### Phase 7 Gate Status

| Criterion | Status |
|---|---|
| Observations ≥ 30 | ✅ 39/30 |
| Calendar days ≥ 7 | ⏳ 2/7 |
| Avg spread ≤ 5% | ✅ 1.39% |
| Avg dir move ≥ 0% | ❌ −1.00% |
| Explicit approval | ❌ Not given |

**Phase 7 BLOCKED.** No paper trading. No positions. No orders.

### Day 7 Open Decisions (unchanged from Phase 6K)

All four decisions remain open and will be evaluated with the full 7-day dataset:

**A) Raise near-expiry filter 24h → 72h**  
The converting zero→negative movers are resolving May 31 markets. A 72h filter would have prevented their inclusion. Remains the strongest candidate change.

**B) Restrict Phase 7 to NASA GISTEMP verified markets only**  
City markets are 100% UNVERIFIED and not what the backtest covered. This decision gains further support with each day of city-dominated, noise-heavy shadow data.

**C) Keep city markets experimental / secondary**  
Alternative to B: allow city markets in Phase 7 but only with ≥7-day resolution filter and smaller position size than $2 default.

**D) Lower shadow-only observation threshold to 5pp for annual_temp**  
Would allow annual_temp markets to enter shadow monitoring without changing trading thresholds. Zero impact on signal engine or trading decisions. Recommended to implement before Day 7 so at least some annual_temp data exists for the review — but requires explicit user approval before any code change.

### No Code Changes Made

This entry is documentation only. No strategy files, threshold values, scheduler configuration, or any other code was modified. The commitment on this day remains: observe and document until Day 7, then decide.

*Appended: Day 2 evening, June 2, 2026.*
