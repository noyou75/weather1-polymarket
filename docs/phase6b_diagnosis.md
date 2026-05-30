# Phase 6B: Backtest Diagnosis & Strategy Calibration Report

**Date:** May 2026  
**Status:** Phase 7 BLOCKED — backtest failed Phase 0 acceptance criteria  
**Readiness:** NEEDS_MORE_DATA  

---

## 1. Backtest Failure Summary

| Criterion | Target | Actual | Status |
|---|---|---|---|
| Win rate | ≥ 52% | 31.0% | ❌ FAIL |
| Max drawdown | < 12% | 2.87% | ✅ PASS |
| Sharpe estimate | > 0.8 | 1.67 | ✅ PASS |
| Min signals | ≥ 30 | 29 entered | ⚠ borderline |
| Kill switch triggers | 0 | 0 | ✅ PASS |
| **Overall** | All pass | **FAIL** | ❌ |

**Data quality: LOW** — entry/exit prices estimated; no historical Polymarket orderbook data.  
**Settlement source: UNVERIFIED** — NASA GISTEMP v4 used as proxy for Polymarket market resolution.

---

## 2. Root Causes of Failure

### Root Cause 1 — Rank-2 Signal is Broken (PRIMARY CAUSE)

The biggest driver of failure is the rank-2 signal ("Will 2026 be the second-hottest year on record?").

| Signal type | Trades | Wins | Losses | Win rate |
|---|---|---|---|---|
| Rank-1 ("hottest year") | 15 | 9 | 6 | **60%** |
| Rank-2 ("second-hottest") | 14 | 0 | 14 | **0%** |
| Combined | 29 | 9 | 20 | 31% |

**Why rank-2 always fails:**  
The Module 2 logic computed rank-2 probability as `(1 - P_rank1) × 0.80`, meaning whenever rank-1 showed a YES signal, rank-2 also showed a YES signal. A year can only occupy ONE rank. When rank-1 is correct (e.g., 2024 was #1), rank-2 is automatically wrong (2024 cannot also be #2). When rank-1 is wrong (e.g., 2020 was #4, not #1), rank-2 is also wrong.

**This is a structural logic flaw, not parameter tuning.** Rank-2+ markets cannot be estimated by complementing rank-1. They require independent models.

### Root Cause 2 — Rank-1 Signal Fires on Small Gaps (secondary)

Two rank-1 false positives reduced win rate from 82% to 60%:

| Year | 3-month GISTEMP avg | Prior record used | Gap | Actual rank | Signal | Result |
|---|---|---|---|---|---|---|
| 2020 | +1.200°C | +1.000°C (fallback) | +0.20°C → 20pp | #4 | YES rank-1 | WRONG |
| 2023 | +1.027°C | +1.008°C (2020) | +0.02°C → ~5pp | #3 | YES rank-1 | WRONG |

- **2020**: No prior full years in dataset (MIN_YEAR=2020). Fallback prior record of +1.000°C is too optimistic. Real context (pre-2020 anomalies) would have shown the year was not exceptional.
- **2023**: Gap of only 5pp triggered a YES signal. 2023 ultimately ranked #3 because 2024 and 2025 were warmer. At small gap sizes, the signal has no predictive power.

**Fix:** Require gap ≥ 10pp. At gap ≥ 10pp, rank-1 win rate rises to **82%** (9/11).

### Root Cause 3 — Settlement Source Uncertainty (structural)

All signals used NASA GISTEMP v4 as the estimator for Polymarket annual temperature rank markets. Polymarket may use NOAA GlobalTemp, NOAA Surface Temperature, or another dataset. If the datasets disagree on the exact annual ranking (which they can, by 0.01–0.05°C margin), a correct GISTEMP-based prediction could still lose against Polymarket's resolution.

This is not a Module 2 calibration problem — it is a **data source risk** that cannot be fixed by parameter tuning. It requires verifying the exact Polymarket resolution source.

### Root Cause 4 — Positive Return Does Not Mean Reliable Edge

The backtest shows +16.88% total return despite 31% win rate. This is explained by **asymmetric payoffs** in binary prediction markets:

- Win: YES token at entry price ~0.45 resolves to 1.0 → **+118.9% return**
- Loss: Stop-loss fires at -15% (capped, doesn't go to full -100%)
- Expected value per trade: (0.31 × 118.9%) + (0.69 × -15.0%) = **+36.9% - 10.4% = +26.5% EV**

The math works out to positive EV **even with low win rate** because the winning trades are very large. However:

- This is based on **estimated entry prices**, not real historical prices
- Actual market prices may have been much higher (closer to 0.70-0.80 by the time our signal fires), reducing the win size dramatically
- A professional Polymarket leaderboard trader (#1 gopfan2) runs ~7.6% efficiency — much lower than our simulated 19.6%, suggesting our estimated prices are too optimistic

**Conclusion:** The positive return is a simulation artifact. Real entry prices would reduce it significantly. Win rate and directional accuracy are more reliable metrics than simulated P&L with estimated prices.

---

## 3. Trade-Level Breakdown

### All 29 Active Trades

| Scenario | Rank | Side | Gap | Entry* | Exit* | P&L% | Outcome | Dir Correct |
|---|---|---|---|---|---|---|---|---|
| 2020-Q1 rank1 | #1 | YES | +20pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2020-Q1 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2020-Q2 rank1 | #1 | YES | +20pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2020-Q2 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2020-Q3 rank1 | #1 | YES | +5pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2020-Q3 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2021-Q1 rank1 | #1 | NO | -30pp | 0.555 | ~0.997 | **+79.1%** | take_profit | ✅ |
| 2021-Q1 rank2 | #2 | YES | +31pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2021-Q2 rank1 | #1 | NO | -30pp | 0.555 | ~0.997 | **+79.1%** | take_profit | ✅ |
| 2021-Q2 rank2 | #2 | YES | +31pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2021-Q3 rank1 | #1 | NO | -30pp | 0.555 | ~0.997 | **+79.1%** | take_profit | ✅ |
| 2021-Q3 rank2 | #2 | YES | +31pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2022-Q1 rank1 | #1 | NO | -10pp | 0.505 | ~0.997 | **+97.0%** | take_profit | ✅ |
| 2022-Q1 rank2 | #2 | YES | +31pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2022-Q2 rank1 | #1 | NO | -30pp | 0.555 | ~0.997 | **+79.1%** | take_profit | ✅ |
| 2022-Q2 rank2 | #2 | YES | +31pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2022-Q3 rank1 | #1 | NO | -10pp | 0.505 | ~0.997 | **+97.0%** | take_profit | ✅ |
| 2022-Q3 rank2 | #2 | YES | +31pp | 0.455 | ~0.387 | **-15.0%** | stop_loss | ❌ |
| 2023-Q1 rank1 | #1 | YES | +5pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2023-Q1 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2023-Q2 rank1 | #1 | YES | +5pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2023-Q2 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2023-Q3 rank1 | #1 | YES | +5pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2023-Q3 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2024-Q1 rank1 | #1 | YES | +20pp | 0.455 | ~0.997 | **+118.9%** | take_profit | ✅ |
| 2024-Q1 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2024-Q2 rank1 | #1 | YES | +20pp | 0.455 | ~0.997 | **+118.9%** | take_profit | ✅ |
| 2024-Q2 rank2 | #2 | YES | +11pp | 0.505 | ~0.430 | **-15.0%** | stop_loss | ❌ |
| 2024-Q3 rank1 | #1 | YES | +20pp | 0.455 | ~0.997 | **+118.9%** | take_profit | ✅ |

*Entry/exit prices are ESTIMATED — no historical Polymarket price data available. Quality: LOW.

**7 additional trades blocked by daily soft stop (triggered by accumulated rank-2 losses).**

---

## 4. Module Attribution Results

| Configuration | Trades | Win Rate | Notes |
|---|---|---|---|
| v1.0 All (rank-1 + rank-2) | 29 | 31.0% | **FAIL** |
| Rank-1 only (all gaps) | 15 | 60.0% | Passes 52% criterion |
| Rank-2 only | 14 | 0.0% | Completely broken — disable |
| Rank-1, gap ≥ 10pp | 11 | **81.8%** | Strong signal — passes with margin |
| Rank-1, gap ≥ 25pp | 4 | 100.0% | Ultra-selective, very few trades |

**Module 4 (wallet confirmation):** All annual temp signals received confirmation (gopfan2, bama124, aenews cluster all specialise here). Module 4 did not help because it confirmed both the correct AND incorrect signals equally.

**Module 5 (liquidity filter):** Correctly passed all 6 tested annual rank markets (liquidity $3K–$20K, spread 0.001–0.02). Liquidity filter is working correctly.

**Direction accuracy by rank:**
- Rank-1: 60% (9/15) — real predictive signal at GISTEMP trajectory level
- Rank-2: 0% (0/14) — no predictive value; logic is structurally flawed

---

## 5. Worst and Best Market Types

### Worst: Rank-2+ Annual Temperature Markets
- **Win rate: 0%**
- Cause: Signal logic is derived from rank-1 complementarily — fundamentally wrong
- **Action: DISABLE entirely in v1.1**

### Worst: Rank-1 at gap < 10pp
- **Win rate: 0%** (0/4 trades at 5pp gap)
- Cause: Gap too small to overcome model uncertainty and inter-year competition
- **Action: Raise minimum gap threshold to 10pp**

### Best: Rank-1 at gap ≥ 10pp  
- **Win rate: 81.8%** (9/11)
- Years tested: 2021, 2022 (NO signals — market NOT hottest), 2024 (YES signal — WAS hottest)
- **Action: Keep as primary signal, with WATCH status until settlement verified**

### Best: Rank-1 at gap ≥ 25pp
- **Win rate: 100%** (4/4)
- Very few trades but perfect accuracy in this limited sample
- **Action: These would be strongest ENTER_CANDIDATE signals after settlement verification**

---

## 6. Strategy v1.1 Recommended Changes

### Disabled Market Types (v1.1)
| Market Type | v1.0 Status | v1.1 Status | Reason |
|---|---|---|---|
| Rank-2 ("second-hottest year") | ENTER_CANDIDATE | **DISABLED** | 0% win rate, broken logic |
| Rank-3+ ("third/fourth/fifth/sixth hottest") | ENTER_CANDIDATE | **DISABLED** | Not backtested; derivative of flawed rank-2 logic |
| Global monthly anomaly (June+) | Evaluated | **DISABLED** | Liquidity < $500 (spread 35-64%); correctly filtered by Module 5 |
| City markets expiring same-day | NEEDS_SETTLEMENT | **DISABLED** | Near-expiry distorts signals; not useful for trading |

### WATCH-Only Market Types (v1.1)
| Market Type | Reason |
|---|---|
| Rank-1 ("hottest year on record") | Settlement source unverified [NEEDS_CHECK]; keep as WATCH until Polymarket resolution source confirmed |
| Global monthly anomaly (May 2026 with good liquidity) | Data not yet published; settlement source unverified |
| City station temp (within 7-day window, supported cities) | NWS/OM are NOT Polymarket settlement source; keep as WATCH |

### Updated Signal Parameters (v1.1)
| Parameter | v1.0 | v1.1 | Rationale |
|---|---|---|---|
| Minimum probability gap for WATCH | 8pp | **10pp** | Eliminates 2023-style false positives |
| Minimum gap for ENTER_CANDIDATE | 8pp | **15pp** | Requires stronger signal to overcome model uncertainty |
| Settlement source verified required for ENTER | No (capped to 60 conf) | **Yes — hard requirement** | GISTEMP ≠ Polymarket resolution source confirmed |
| Rank-2+ markets | Evaluated | **SKIP_UNSUPPORTED_TYPE** | Disable entirely |
| City markets expiring < 24h | Module 5 filters via spread | **Explicit same-day exclusion** | Near-expiry creates distorted signals |
| Minimum prior years in GISTEMP | None | **≥ 3 full prior years** | Prevents 2020-style no-context false positives |
| Module 4 confirmation required for ENTER | No (additive confidence) | **Soft requirement for rank-1** | Prevents false signals from proceeding without specialist confirmation |

### v1.1 Projected Backtest Performance
With rank-1 only, gap ≥ 10pp:
- **Win rate: 81.8%** ✅ (vs 52% threshold)
- **Simulated return: +16.75%** (estimated prices — LOW quality)
- **Max drawdown: < 3%** ✅
- **Kill switch triggers: 0** ✅

⚠ This projection uses estimated prices and limited GISTEMP data. Quality remains LOW until historical Polymarket price data and verified settlement source are available. **Phase 7 is not approved on this projection alone.**

---

## 7. Data Improvement Plan

The following data is required before a valid backtest that could approve Phase 7:

### Critical (Phase 7 is blocked without these)

| Data Required | Purpose | How to Obtain |
|---|---|---|
| **Verified Polymarket settlement source** for annual/monthly temp markets | Confirms whether GISTEMP, NOAA GlobalTemp, or another dataset is used | Review Polymarket market description/resolution criteria for specific market IDs; check UMA oracle settlement records |
| **Historical Polymarket trade prices** for resolved weather markets | Replace estimated entry/exit prices with real market prices | Polymarket Data API (`/trades` endpoint for resolved markets); check `closed=true` query |
| **Resolved market outcome records** | Confirm YES/NO resolution for each historical market | Polymarket Data API or on-chain resolution events |

### Important (improves backtest quality from LOW to MEDIUM/HIGH)

| Data Required | Purpose | How to Obtain |
|---|---|---|
| True archived NWS forecasts | Enable honest Module 2 city-temp backtesting | NOAA archives / Iowa Environmental Mesonet historical forecasts |
| More prior GISTEMP context (pre-2020) | Eliminates 2020-style no-prior-context false positives | Already in GISTEMP CSV — lower MIN_YEAR in noaa.py from 2020 to 2000 |
| City station temperature historical market prices | Enable city-temp backtest | Polymarket historical trade data API |
| Station mapping for Chinese/Asian cities | Many Polymarket city temp markets use non-US cities not in NWS seed | Add Open-Meteo stations for Hong Kong, Seoul, Tokyo, etc. |

### Nice to Have (Phase 6 enhancement)

| Data Required | Purpose |
|---|---|
| Intraday GISTEMP preliminary estimates | Better signal timing within year |
| Top wallet historical position timestamps | Enable Module 4 live backtest |
| Polycool/Notion leaderboard data | Expand wallet watchlist context |

---

## 8. Why Phase 7 Remains Blocked

Phase 7 requires **all** of these Phase 0 Section 8.10 criteria to pass:

1. ❌ **Win rate ≥ 52%**: v1.0 scored 31%. v1.1 projects 82% but this is based on estimated prices (LOW quality data). Real prices could reduce win size and change the result.
2. ⚠ **Settlement source verified**: GISTEMP is unverified as Polymarket resolution source. A correct GISTEMP-based signal could still lose at Polymarket settlement if datasets disagree.
3. ⚠ **Minimum 30 signals**: v1.0 had 29 entered trades (borderline). v1.1 with rank-1 + gap≥10pp would have only 11 trades — **below the 30 minimum**.
4. ⚠ **Historical price quality**: Entry prices were estimated at 0.45–0.55. Real market prices for well-known years (2024 hottest year) may have been 0.70–0.85 by Q1, greatly reducing win size.

**To unblock Phase 7, at minimum:**
1. Verify Polymarket settlement source for annual temperature rank markets
2. Obtain historical prices for at least 30 resolved weather markets
3. Re-run backtest with real price data showing win rate ≥ 52%
4. Lower MIN_YEAR in `noaa.py` to 2000 to expand GISTEMP context and signal count

---

## 9. Conclusion

Strategy v1.0 failed due to one structural flaw (broken rank-2 logic) and one calibration issue (gap threshold too low). These are fixable. Strategy v1.1 shows strong projected performance but cannot be verified without real historical price data and confirmed settlement source.

**Phase 7 BLOCKED — proceed with data collection, v1.1 implementation, and re-backtest before paper trading.**
