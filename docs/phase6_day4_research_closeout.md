# Phase 6 — Shadow Research Closeout (Day 4 Cutoff)
**Date written:** June 2026  
**Research window:** Day 1 (May 30, 2026) through Day 4 (June 2, 2026)  
**Status:** RESEARCH CLOSED — Phase 7 BLOCKED

---

## 1. Research Cutoff

**The official research decision window is Day 1 through Day 4 only.**

Day 5–Day 7 data must not be used for the final Phase 7 decision in this review cycle.

**Reason:** After Day 4 (June 2, 2026), the shadow monitoring system experienced a freeze caused by a design gap: when the latest SignalRun contained 0 qualifying observable signals, the shadow observer stopped updating all existing observations. This was discovered on June 2 and corrected by Option C (commit `50c3952`), which decoupled existing observation price tracking from signal generation. The infrastructure repair — deactivating 45 resolved markets, updating the remaining 19 active ones, and correcting the daily summary — changed the observable lifecycle of the dataset. Any data collected after Option C's deployment reflects a corrected but structurally different observation cadence.

Day 1–4 data was collected under consistent, uninterrupted conditions and is sufficient to reach a clear strategic conclusion.

---

## 2. Project Status at Research Cutoff (Day 4)

| Metric | Value |
|---|---|
| Total shadow observations | **64** |
| Calendar days observed | **4 of 7** |
| Total snapshots (before Option C) | **2,633** |
| Total snapshots (after Option C verification) | **2,697** |
| Avg spread at observation time | **1.46%** |
| Headline Avg Directional Move | **+7.63%** |
| Positive movers | 25 |
| Negative movers | 31 |
| Zero movers | 8 |
| Scheduler | Running |
| Phase 7 status | **BLOCKED** |
| Annual_temp observations | 0 |
| Decision D triggered | No (gap ~1.5pp, below 5pp threshold) |
| ENTER_CANDIDATE created | 0 |

---

## 3. Data-Quality Note — Why the Headline Average Is Misleading

The dashboard headline of **+7.63% Avg Directional Move** must not be read as confirmation of a positive strategy edge. Three compounding problems make this number unreliable as a standalone decision metric:

**Problem 1 — Outlier concentration:** The positive average is driven by 3–5 micro-price markets that moved +100% to +340%. These are not systematic wins; they are lottery-ticket outcomes from markets priced at 0.1%–3% probability where small absolute moves generate enormous percentage moves.

**Problem 2 — Blended active/finalized confusion:** The dashboard average combines observations that are still live (pre-resolution, unknown outcome) with observations that have already resolved. These two populations have fundamentally different interpretation requirements.

**Problem 3 — Median divergence:** The median Directional Move remained **0.00%** across all four days. The mean (+7.63%) and median (0.00%) are separated by 7.63 percentage points — a gap almost entirely explained by the extreme outlier winners.

**Correct reading:** the finalized/resolved observations are the ground truth. Finalized markets have settled; their directional moves are terminal, not speculative. The finalized dataset, once separated from the still-live set by Option C, tells a materially different story than the blended headline.

---

## 4. City_station_temp Final Finding — Edge NOT Confirmed

### Composition
- 100% of all 64 shadow observations were **city_station_temp** markets
- Settlement source for all: **UNVERIFIED (NEEDS_SETTLEMENT_SOURCE_CHECK)**
- NWS forecast data was the signal source; Polymarket's actual resolution source for city temperature markets was never confirmed

### Finalized / Inactive Set (45 observations — markets that have resolved)

| Metric | Value |
|---|---|
| Total finalized observations | 45 |
| Correct direction (resolved win) | 9 |
| Incorrect direction (resolved loss) | 35 |
| Unresolved at deactivation | 1 |
| **Resolved win rate** | **9/44 = 20.5%** |
| Avg directional move | **−22.92%** |
| **Median directional move** | **−96.55%** |

The median of −96.55% reveals the true picture: the typical resolved city temperature market went to near-zero (wrong temperature range predicted). Only 9 of 44 resolved markets were correct.

### Active Set at Day 4 Cutoff (19 observations — markets still open)

| Metric | Value |
|---|---|
| Active observations | 19 |
| Positive movers | 7 |
| Negative movers | 10 |
| Zero movers | 2 |
| **Active win rate (non-zero)** | **7/17 = 41.2%** |
| Avg directional move | **−1.08%** |
| **Median directional move** | **−13.58%** |
| Trimmed average (±2 removed) | **−8.35%** |

The active set is already trending negative before resolution. Median −13.58% and trimmed average −8.35% both indicate negative central tendency for the markets that have not yet resolved.

### Conclusion

**City_station_temp edge is NOT confirmed.**

The evidence is unambiguous on resolved markets: 20.5% resolution win rate, median −96.55%. The strategy needs >52% win rate to pass Phase 0 acceptance criteria. The gap between required (52%) and observed (20.5%) is too large to attribute to sampling noise over 44 resolved observations.

---

## 5. Outlier Analysis — Why +7.63% Is Fragile

Day 4 headline of +7.63% Avg Directional Move was entirely driven by a small number of micro-price outliers:

| Scenario | Avg Dir Move |
|---|---|
| All 64 observations (baseline) | **+7.63%** |
| Remove top 1 winner (+340%) | +2.36% |
| **Remove top 3 winners** | **−4.04%** |
| Remove top 5 winners | −7.49% |
| **Trimmed ±3 (remove top 3 + bottom 3)** | **−0.68%** |
| Median (all 64) | **0.00%** |

### Price floor test (realistic entry thresholds)

| Min Entry Price | Avg Dir Move | Assessment |
|---|---|---|
| No floor | +7.63% | Outlier-driven |
| ≥ $0.03 | **−0.73%** | Negative |
| ≥ $0.05 | **−0.64%** | Negative |
| ≥ $0.10 | +2.89% | Marginally positive |
| ≥ $0.20 | **−1.03%** | Negative |

At every realistic entry price floor except $0.10, the performance is negative. The $0.10 result (+2.89%) is thin and within noise range given the sample size.

### Conclusion

The positive headline was produced by 3–5 markets priced at 0.1%–3% probability, where winning means a 100–340% move and losing means a −97 to −100% move. These are not indicative of systematic edge. They are high-variance outliers in a distribution where the central tendency (median 0%, trimmed average −0.68%) is neutral to negative.

**City market headline gains were outlier-driven and not robust.**

---

## 6. Annual_temp / NASA GISTEMP Finding

### Settlement source — CONFIRMED
Verified from 11 closed Polymarket market descriptions (Phase 6D, June 2026):
> *"This market will resolve...if the data for the Global Land-Ocean Temperature Index..."*

**NASA GISTEMP v4 (Global Land-Ocean Temperature Index) is the confirmed Polymarket settlement source for all annual and monthly global temperature markets.**

### Shadow observations — ZERO during review
Annual_temp generated 0 shadow observations during Days 1–4. The signal engine evaluated the "Will 2026 be the hottest year on record?" market and produced `NEEDS_MORE_DATA` because the probability gap was below the shadow-only threshold:
- Model estimated probability: ~35%
- Market implied probability: ~33.5%
- Gap: ~1.5pp
- Decision D threshold: 5pp minimum
- Trading threshold (MIN_GAP_WATCH): 10pp minimum

The gap narrowed from ~7.5pp (Phase 6K assessment, pre-Day 1) to ~1.5pp by Day 4 as the market repriced toward the model estimate. Decision D did not trigger during the entire research window.

### Backtest result (from Phase 6 — for reference)
- Strategy v1.1: rank-1 only ("hottest year on record"), gap ≥ 10pp, ≥ 3 prior years GISTEMP context
- Backtest win rate: **71.4%** (11 trades, MEDIUM quality data)
- Data quality: MEDIUM (verified settlement source; estimated entry prices — no real historical CLOB prices available)

### Conclusion
Annual_temp is the only validated, settlement-verified strategy family in this project. However, it had zero observable signal during the shadow research window because the market gap was too small to cross any threshold. This is not a failure of the strategy; it is the correct behavior of a disciplined threshold system. **Annual_temp was valid in principle but had no actionable gap during this window.**

---

## 7. Decision D Status

| Item | Detail |
|---|---|
| Commit | `0bc05fb` |
| Purpose | Shadow-only observer for annual_temp markets with gap 5–10pp |
| Files changed | `backend/strategy/shadow_observer.py` only |
| Trading thresholds changed | None |
| ENTER_CANDIDATE created | 0 |
| SHADOW_WATCH_VERIFIED_LOW_GAP triggered | 0 (gap ~1.5pp < 5pp threshold) |
| Safety status | Safe and passive — dormant during review |

Decision D is deployed and will activate automatically if the annual_temp gap widens back above 5pp. It requires no action.

---

## 8. Option C Status

| Item | Detail |
|---|---|
| Commit | `50c3952` |
| Purpose | Decouple existing observation price tracking from signal generation |
| Problem fixed | Shadow observer froze when SignalRun had 0 qualifying signals (June 1 23:48 UTC) |
| Effect on data | Updated 64 observations, added 64 snapshots, deactivated 45 resolved markets, left 19 active |
| Classification | **Infrastructure repair — not strategy improvement** |

Option C is a data-quality correction that took effect after the Day 4 research window closed. The deactivation of 45 resolved observations and the active/finalized split it revealed provide retrospective clarity on the Day 1–4 dataset, but the correction itself is not part of the research evidence. It is treated as a housekeeping fix applied after the research window.

---

## 9. Final Decision

### Phase 7 paper trading: DO NOT START

The shadow research (Days 1–4) does not provide sufficient evidence to approve Phase 7 paper trading. The specific reasons:

1. **City_station_temp**: Resolved win rate 20.5% — far below the 52% Phase 0 acceptance criterion
2. **Annual_temp**: Zero shadow observations; strategy valid but no actionable gap during the window
3. **Headline metric was misleading**: +7.63% blended average was driven by outliers; trimmed average and median were near zero or negative
4. **Settlement source unverified for city markets**: NWS is not confirmed as Polymarket's resolution source for city temperature markets

### City_station_temp: Excluded from Core Phase 7

City temperature markets must not be included in the core Phase 7 paper trading strategy.

If city markets are ever included as **experimental/secondary** in a future design, the minimum constraints are:
- Entry price ≥ $0.10 (filters micro-price lottery markets)
- Time to resolution ≥ 7 days (eliminates near-expiry noise)
- Position size maximum: $1 (half the default $2)
- Completely separate experimental P&L tracking (not blended with core strategy)
- Explicit settlement risk label on every paper position
- No ENTER_CANDIDATE without verified settlement source

### Core Phase 7 design (if ever restarted): Annual_temp / NASA GISTEMP only

- Only annual temperature rank markets ("hottest year on record") qualify for core Phase 7
- Settlement source: verified NASA GISTEMP v4
- Entry criterion: gap ≥ 10pp (MIN_GAP_WATCH — unchanged)
- No gap = no trade. Correct decision when gap is below threshold is: wait.
- If the "Will 2026 be hottest year?" market gap remains at ~1.5pp, there is no qualifying trade

---

## 10. Recommended Next Roadmap

The research window is closed. The following actions are recommended before any Phase 7 discussion is reopened:

**Immediate:**
- Archive this Day 1–4 shadow research as the canonical evidence base
- Stop referencing the blended headline Avg Dir Move (+7.63%) as a positive signal
- The correct summary of Day 1–4 is: *city markets failed; annual_temp had no observable gap*

**Next phases if project continues:**

| Phase | Description | Priority |
|---|---|---|
| A | Build active vs finalized dashboard split — show resolved win rate separately from live directional moves | High |
| B | City settlement-source verification research — determine whether Polymarket uses NWS, a specific weather station, or another source for city temp markets | High |
| C | Annual_temp monitoring dashboard — track the "hottest year" gap daily, alert when it returns above 5pp or 10pp | Medium |
| D | Market cleanup / stale market handling — prevent resolved markets from accumulating in the DB and polluting the signal engine | Medium |
| E | New Phase 7 design for NASA GISTEMP markets only — write a fresh paper trading plan when annual_temp gap exceeds 10pp and shadow data (with verified prices) exists | Later |

**Do not proceed directly to Phase 7.** The next step after this closeout is redesign, not activation.

---

## 11. Safety Statement

The following constraints remain in force and are not changed by this closeout document:

- **No paper trading approved.** Phase 7 is not activated.
- **No real trading approved.** No orders have been or will be placed.
- **No orders.** No CLOB order endpoints were called at any point in this project.
- **No private keys.** No wallet credentials, mnemonics, or signing keys exist in this codebase.
- **No wallet execution.** No transaction signing, order submission, or on-chain interaction was implemented.
- **Phase 7 remains BLOCKED.** This document closes the research window and records the decision not to proceed.

The Weather1 system as of this closeout is a read-only research and shadow monitoring tool. It has produced valuable negative evidence: city_station_temp does not have a confirmed edge under the conditions tested in Days 1–4.

---

*Document written: Phase 6 closeout, June 2026.*  
*Research period: Day 1 (May 30) – Day 4 (June 2), 2026.*  
*Next action: redesign, not Phase 7 activation.*
