# Locked Requirement: Future Test Protocol — Portfolio-Style Tracking
**Status:** LOCKED — applies to all future Weather1 test phases  
**Date recorded:** June 2026  
**Authority:** User decision, post-Day-4 research closeout  

---

## Purpose

This document records a locked product and research requirement for Weather1.

Any future multi-day test, simulation, shadow-to-paper phase, or paper trading phase **must use a defined starting capital and must track all results as real portfolio-style dollar numbers**, not only as directional-move percentages.

The Day 1–4 shadow research period demonstrated the risk of using a single blended metric (Avg Directional Move) as a proxy for trading performance. That metric was misleading:
- Headline showed +7.63% while the finalized resolved win rate was 20.5%
- The blended average combined unresolved and resolved markets without distinguishing them
- No capital-at-risk, fee, or slippage tracking existed
- No entry/exit reasoning was recorded

This requirement prevents that failure mode from recurring.

---

## 1. Defined Starting Test Capital

- Default starting test capital: **$100** (paper/simulated funds only)
- This amount can only be changed by explicit written user approval
- The amount must be displayed prominently on the dashboard at all times
- If no approval is given, all future tests default to $100 starting capital

---

## 2. Required Tracking Fields

Every future test phase must track and display all of the following. Directional-move percentage alone is insufficient.

### Account Level

| Field | Description |
|---|---|
| Starting capital | Fixed at phase start, displayed throughout |
| Cash balance | Capital not currently deployed |
| Open exposure | Total capital currently at risk in open positions |
| Total equity | Cash balance + mark-to-market value of open positions |
| Realized PnL ($) | Dollar profit/loss from closed positions |
| Unrealized PnL ($) | Dollar mark-to-market gain/loss on open positions |
| Total return (%) | (Current equity − Starting capital) / Starting capital |
| Max drawdown (%) | Largest peak-to-trough equity decline since start |
| Win count | Number of closed positions with positive realized PnL |
| Loss count | Number of closed positions with negative realized PnL |
| Win rate (%) | Win count / (Win count + Loss count) |

### Position Level

Every individual position must record:

| Field | Description |
|---|---|
| Market ID | Polymarket market identifier |
| Question | Full market question |
| Market type | annual_temp / city_station_temp / etc. |
| Settlement source | VERIFIED_NASA_GISTEMP / UNVERIFIED / etc. |
| Side | YES or NO |
| Entry price | Price at position open (ask + slippage) |
| Position size ($) | Dollars deployed |
| Entry time | UTC timestamp |
| Entry reason | Which modules triggered; gap size; confidence score |
| Current price | Latest mid-price (mark-to-market) |
| Unrealized PnL ($) | (Current price − Entry price) / Entry price × Size |
| Stop-loss level | Price at which stop fires |
| Take-profit targets | +10% / +20% / +40% levels |
| Exit price | Price at position close |
| Exit time | UTC timestamp |
| Exit reason | Take-profit tier / stop-loss / near-expiry / manual |
| Realized PnL ($) | Dollar profit or loss after close |
| Realized return (%) | Realized PnL / Position size |
| Spread cost ($) | Estimated bid-ask spread cost paid |
| Slippage cost ($) | Simulated slippage applied |
| Fees ($) | Estimated taker fee (if applicable) |
| Net PnL ($) | Realized PnL − spread cost − slippage − fees |

---

## 3. Cost and Slippage Assumptions (Locked Defaults)

These assumptions apply until changed by explicit user approval:

| Cost type | Default assumption |
|---|---|
| Entry slippage | 1.0% of mid-price |
| Exit slippage | 0.5% of mid-price |
| Near-resolution extra slippage | 1.5% additional (within 48h of resolution) |
| Taker fee | 0% (Polymarket does not charge taker fees on binary markets as of 2026) [NEEDS_CHECK] |
| Spread cost | Bid-ask spread at entry, recorded per position |

All three cost items (slippage, fees, spread) must be recorded separately and deducted before reporting net PnL.

---

## 4. Risk Rules — Enforced in All Future Tests

These rules come from Phase 0 Section 7 and are locked. They must be enforced programmatically in any future paper trading simulator, not just displayed:

| Rule | Value | Enforcement |
|---|---|---|
| Starting capital | $100 (default) | Hard-coded at test start |
| Default position size | $2 | Per signal, unless elevated criteria met |
| Elevated position size | $3 | Only when Module 1+2+4 all confirm |
| Maximum position size | $5 | Absolute cap, no exceptions |
| Maximum open exposure | $35 | No new positions if at or above |
| Daily soft stop | −$7 (−7%) | No new entries for rest of UTC day |
| Portfolio kill switch | −$15 (−15%) | HALTED state; manual review required |
| Stop-loss per position | −15% of position value | Fires automatically |
| No averaging down | Prohibited | Cannot add to a losing position |
| Averaging down override | Only with explicit written user approval per instance | |

---

## 5. Prohibited Metrics as Sole Performance Indicators

The following metrics must never be used alone as the primary measure of test performance:

| Metric | Reason it is insufficient alone |
|---|---|
| Avg Directional Move (%) | Blends unresolved and resolved; inflated by outliers; no capital context |
| Positive/negative mover count | No magnitude; a small win and a large loss have the same count |
| Headline return with estimated prices | Estimated entry prices produce unreliable P&L; must label clearly |

These metrics may still be reported as supplementary context but must always be accompanied by the portfolio-level dollar metrics in Section 2.

---

## 6. Required Questions — Every Test Must Answer

At any point during or after a future test, the system must be able to answer all of the following. If any cannot be answered, the test is not properly instrumented:

1. **What was the starting capital?**
2. **What is the current capital (equity)?**
3. **What is the profit or loss in dollars?**
4. **How much capital is currently at risk (open exposure)?**
5. **What were the estimated fees and costs for each position?**
6. **Why did the system enter this position?** (modules, gap size, confidence, settlement source)
7. **Why did the system exit this position?** (take-profit tier, stop-loss, near-expiry, manual close)

---

## 7. Dashboard Display Requirements

Any future dashboard page for paper trading or simulation must show:

- Starting capital: prominently at top
- Current equity: prominently at top
- Cash available: displayed
- Open exposure bar (vs $35 limit)
- Drawdown gauge (vs 15% kill switch)
- Daily loss counter (vs 7% daily stop)
- Risk state: GREEN / YELLOW / RED / HALTED
- Open positions table (with all position-level fields)
- Closed positions table (with realized PnL, net of costs)
- Portfolio equity curve (dollar values, not percentage moves)
- Win/loss record with percentages
- Clear label distinguishing estimated prices vs real prices

**Avg Directional Move may appear as a supplementary metric but must never be the primary portfolio performance indicator.**

---

## 8. What This Requirement Does NOT Do

This is a locked requirement for future redesign. It does not:

- Enable paper trading (Phase 7 remains BLOCKED)
- Add order execution, wallet, or private key logic
- Change any current strategy thresholds
- Change the current scheduler or signal engine
- Approve any market type for Phase 7

This document is a specification that must be satisfied **before** any future test phase is approved.

---

## 9. Future Phase Approval Gate

Before any future test phase (paper trading, shadow-to-paper, experimental PnL, or live pilot) is approved:

- [ ] This requirement document must be acknowledged
- [ ] All 17 tracking fields in Section 2 must be implemented in the simulator
- [ ] Risk rules in Section 4 must be enforced programmatically (not just displayed)
- [ ] Costs in Section 3 must be applied to every position
- [ ] The dashboard must show dollar equity, not only directional move percentages
- [ ] Explicit written user approval must be given for that specific phase
- [ ] Phase 7 BLOCKED status must be explicitly lifted by the user

---

## Safety Statement

- No paper trading approved by this document.
- No real trading approved by this document.
- No orders.
- No private keys.
- No wallet execution.
- Phase 7 remains BLOCKED.
- This document is a specification only.

---

*Recorded: Phase 6 research closeout, June 2026.*  
*Applies to: all future Weather1 test, simulation, paper, or live phases.*  
*Override authority: explicit written user approval only.*
