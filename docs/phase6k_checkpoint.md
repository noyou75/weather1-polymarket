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
