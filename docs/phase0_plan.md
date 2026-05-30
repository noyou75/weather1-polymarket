# Phase 0: Weather1 — Polymarket Weather Edge Engine
## Implementation Plan — May 2026

> **Status:** Approved. Phase 1 in progress.  
> **Labels:** [FROM_ATTACHED_FILES] · [INFERENCE] · [FROM PROJECT BRIEF] · [NEEDS_CHECK]

---

## 1. Source Review

### 1.1 Polymarket Repository Guide (Pasted text)
**Summary:** Categorized breakdown of Polymarket's official and community GitHub repositories. Covers the core Python SDK (`py-clob-client`, 838 stars), the JavaScript CLOB client, market-data tools, subgraph connectors, analytics dashboards, arbitrage bots, and market-making frameworks. Includes explicit security warnings about unaudited community repos.

**Key Technical Implications:**
- `py-clob-client` is the canonical Python SDK. Handles order placement, cancellation, orderbook queries, and L1/L2 authentication. [FROM_ATTACHED_FILES]
- CLOB operates on Polygon PoS with USDC collateral. Two-tier auth: L1 (on-chain wallet signature) and L2 (derived API key). [FROM_ATTACHED_FILES]
- Separate **Gamma API** for market metadata. Separate **Polymarket Data API** for historical trades/PnL/leaderboard. [FROM_ATTACHED_FILES]
- WebSocket streams available for real-time orderbook updates. [FROM_ATTACHED_FILES]
- Community repos for arbitrage/market-making exist but carry explicit security warnings. [FROM_ATTACHED_FILES]

**Key Trading Implications:**
- Phase 1 (read-only dashboard) needs only Gamma API + Data API — no authentication. [INFERENCE]
- L1/L2 authentication setup only in Phase 8. Never in Phase 1–7.
- CLOB limit orders allow realistic fill simulation for paper trading. [INFERENCE]

**[NEEDS_CHECK]:** Current base URLs for CLOB V2, Gamma API, Data API · Whether CLOB V1 is fully sunset · Official rate limits · Whether any sandbox/testnet exists.

---

### 1.2 Top 100 Weather Traders HTML
**Summary:** All-time PnL leaderboard for Polymarket Weather category, May 2026. 100 wallet records with: rank, wallet address, username, X handle, PnL, volume, efficiency (PnL÷Volume×100), strategy badges, and detailed strategy analysis. [FROM_ATTACHED_FILES]

**Key stats:** #1 gopfan2 +$350,530 · Top-100 combined +$3,087,043 · #50 threshold +$21,940 · Highest efficiency: DarbySkees 50% · Highest volume: dpnd $12.2M. [FROM_ATTACHED_FILES]

**Key Trading Implications:**
- Dominant edge: global monthly/annual temperature anomaly markets. [FROM_ATTACHED_FILES]
- High efficiency (>10%) achievable at low volume — DarbySkees, MrFox, MtnMark all under $120K total volume. [FROM_ATTACHED_FILES]
- Multi-wallet operations not replicable at $100 scale. [INFERENCE]

---

### 1.3 7-Day Claude Mastery Plan PDF
**Summary:** Structured guide for using Claude effectively. Covers prompt architecture, structured output, uncertainty handling, iterative refinement.

**Principles applied:**
| Principle | Application |
|---|---|
| Clear context | Every module documents its data source and assumptions |
| Structured output | Signal engine returns scored JSON, not free text |
| Uncertainty handling | All signals carry confidence score; low-confidence filtered |
| Step-by-step work | Phase-gated development |
| Citations | Every signal references source data |
| Risk review | Dedicated Risk Monitor; kill switch enforced programmatically |
| Iterative refinement | Backtest → paper → review → adjust loop |

---

## 2. Top 100 Weather Trader Analysis

### 2.1 Top-50 Threshold
| Metric | Value |
|---|---|
| #50 trader | vip68 |
| #50 PnL | +$21,940 |
| #50 Volume | $2,397,681 |
| #50 Efficiency | 0.91% |
| #1 PnL | +$350,530 |
| Top-100 combined | +$3,087,043 |

### 2.2 Strategy Type Distribution
| Strategy | Count | Avg PnL | Avg Efficiency |
|---|---|---|---|
| Sharp Selector | 46 | ~$35K | ~12% |
| Swing Trader | 45 | ~$22K | ~2% |
| Volume Whale | 25 | ~$28K | ~0.7% |
| Multi-Wallet | 11 | ~$85K | ~5% |
| Bot / Algo | 7 | ~$32K | ~2.3% |
| Domain Expert | 7 | ~$28K | ~5% |

### 2.3 High-Efficiency Traders (>10%)
| Rank | Username | PnL | Volume | Efficiency |
|---|---|---|---|---|
| 52 | DarbySkees | $21,458 | $42,915 | 50.0% |
| 88 | MtnMark | $15,404 | $52,941 | 29.1% |
| 18 | CoffeeLover | $51,105 | $161,054 | 31.7% |
| 86 | Miojinho | $15,613 | $69,002 | 22.6% |
| 97 | mkuu | $13,556 | $62,875 | 21.6% |
| 5 | bama124 | $86,600 | $410,556 | 21.1% |
| 56 | InsiderrrZ | $20,527 | $102,163 | 20.1% |
| 65 | xX25Xx | $18,841 | $93,610 | 20.1% |
| 53 | MrFox | $21,382 | $113,878 | 18.8% |
| 96 | ocelot-204 | $13,662 | $83,819 | 16.3% |

**Pattern:** Every trader above 10% efficiency is a Sharp Selector with volume under $750K. Few trades, high conviction. [INFERENCE]

### 2.4 Multi-Wallet Clusters
| Cluster | Wallets | Combined PnL | Combined Volume |
|---|---|---|---|
| gopfan | gopfan2 (#1), gopfan (#4) | ~$469K | ~$5.34M |
| aenews | aenews2 (#2), aenews-915 (#15), chilling (#19) | ~$394K | ~$11.4M |
| HondaCivic | HondaCivic (#12), EngineOfHondaCivic (#43), TiresOfHondaCivic (#68) | ~$102K | ~$9.4M |
| Protrade | Protrade2 (#24), protrade3 (#27) | ~$73K | ~$3.46M |

### 2.5 Copyable with $100
| Strategy | Why Copyable | Target Traders |
|---|---|---|
| Global temp record bets | Requires NOAA/NASA data literacy, not capital scale | gopfan2, bama124, ANudeEgg |
| City/station-specific temp markets | Small markets, $2–$5 positions meaningful | 9985 |
| Selective entry on strong forecast consensus | Signal-driven, no volume requirement | CoffeeLover, MrFox, DarbySkees |
| Late-stage probability capture | Low remaining risk, defined downside | Brokie, Railbird |

### 2.6 Avoid at $100 Scale
| Strategy | Why Avoid |
|---|---|
| Market making / liquidity provision | Requires $50K+ deployed capital |
| High-volume systematic algo (1% efficiency) | At $100, 1% = $1 on full deployment |
| Multi-wallet cluster | No benefit below $5K per wallet |
| Single mega-trade concentration | Requires $50K+ |

---

## 3. Strategy Thesis — Version 1

### Module Overview
| # | Module | Purpose | Priority | Complexity |
|---|---|---|---|---|
| 1 | Global/Station Temperature Edge | Primary signal generator | P0 | Medium |
| 2 | Forecast vs Market Probability Gap | Entry trigger | P0 | Medium |
| 3 | Late-Stage Profit Capture | Exit manager | P0 | Low |
| 4 | Top-Wallet Confirmation | Secondary filter | P1 | Low |
| 5 | Liquidity/Spread Filter | Trade gate | P0 | Low |
| 6 | Risk Engine & Kill Switch | Hard guardrail | P0 | Low |
| 7 | Paper-Trading Simulator | Execution layer | P0 | Medium |

### Module Descriptions

**Module 1 — Global/Station Temperature Edge**
Inputs: NOAA/NASA GISTEMP monthly anomaly; NWS station forecasts; Open-Meteo ERA5 historical context.
Entry: global record markets → enter YES if current anomaly tracking ≥0.10°C above prior record with ≥15 days elapsed. City markets → enter if NWS 72h forecast CI falls entirely above/below threshold.
Required: model agreement ≥80% across ≥2 independent sources.

**Module 2 — Forecast vs Market Probability Gap**
Inputs: Polymarket CLOB live mid-price; Open-Meteo ensemble probability; NWS probability.
Entry: gap between model probability and market implied probability ≥10 percentage points, consistent across ≥2 sources.

**Module 3 — Late-Stage Profit Capture**
Not an entry module. Manages exits: +10% → close 50%; +20% → close additional 25%; +40% → close remaining. 48h pre-resolution = re-evaluation checkpoint (not forced close). Close if edge weakened, liquidity poor, or settlement risk high. Small remainder allowed if confidence high and risk limits respected.

**Module 4 — Top-Wallet Confirmation**
Watchlist: gopfan2, bama124, ANudeEgg, CoffeeLover, DarbySkees, MrFox, 9985.
Confirmation only — never primary trigger. Only wallets with >8% all-time efficiency count. We copy Sharp Selector logic, not volume scale.

**Module 5 — Liquidity/Spread Filter**
Hard gate: skip if total liquidity <$500 · spread >5% · fewer than 10 resting orders · last trade >6h ago · resolution within 24h.

**Module 6 — Risk Engine**
Enforces: max exposure $35 · daily stop $7 · kill switch at $15 drawdown · take-profit ladder · stop-loss –15% per position.

**Module 7 — Paper Trading Simulator**
Fill simulation: buy YES at best-ask + 1% slippage; sell at best-bid + 0.5% slippage. Mark positions to market every 15 minutes. No real orders ever.

---

## 4. Weather Data Plan

| Source | Purpose | Auth | Free | Freshness | Priority | Settlement Match |
|---|---|---|---|---|---|---|
| Polymarket Gamma API | Market discovery | None | Yes | 4h poll | P0 | N/A |
| Polymarket CLOB REST | Live prices, orderbook | None (reads) [NEEDS_CHECK] | Yes | 5min poll | P0 | N/A |
| Polymarket Data API | Wallet history, backtest | None [NEEDS_CHECK] | Yes | 30min poll | P0/P1 | N/A |
| NWS API | City/station forecasts | None | Yes | 6h (model runs) | P0 | US city markets |
| NOAA GISTEMP / NOAAGlobalTemp | Global anomaly data | CDO token [NEEDS_CHECK] | Yes | Monthly | P0 | Primary settlement source |
| Open-Meteo Forecast | Probability gap calculation | None | Yes | 6h | P0 | Secondary reference |
| Open-Meteo ERA5 | Historical reanalysis for context | None | Yes | Static | P1 | NOT true forecast [NEEDS_CHECK] |
| Top 100 wallet JSON | Module 4 watchlist | Local file | Yes | Manual update | P1 | N/A |
| minuteTemp | Intraday city markets | [NEEDS_CHECK] | [NEEDS_CHECK] | Per-minute | P2 | City intraday only |
| Polycool/Notion | Extended trader data | [NEEDS_CHECK] | [NEEDS_CHECK] | Manual | P2 | N/A |

**Important:** ERA5 is hindcast/reanalysis, NOT the true forecast available at time T. For Module 2 historical backtesting, true archived forecast data is needed. [NEEDS_CHECK — source for archived NWS/ECMWF forecasts]

---

## 5. Dashboard Product Plan

| Page | Key Metrics | Key Components | Data Sources | Priority |
|---|---|---|---|---|
| 1. Overview | Capital, daily P&L, equity curve, active signals | Stat cards, equity line chart, top-3 positions table | Paper DB, Risk engine | P0 |
| 2. Live Weather Markets | Active markets, prices, spreads, resolution dates | Market table with filters, signal flags | Gamma API, CLOB | P0 |
| 3. Signal Scanner | Signals above threshold, gap size, confidence scores | Scored signal table, gap histogram | All ingestion modules | P0 |
| 4. Paper Portfolio | Capital, P&L, open/closed positions, win rate | Open positions table, closed trades table, P&L chart | Paper trading DB | P0 |
| 5. Risk Monitor | Drawdown %, daily loss %, exposure, kill switch state | Gauge cards, exposure bar, HALTED banner | Risk engine | P0 |
| 6. Top Wallet Tracker | Watchlist activity, recent trades, signal alignment | Wallet table, trade history | Top 100 JSON, Data API | P1 |
| 7. Backtest Reports | Win rate, Sharpe, drawdown, equity curve | Results table, equity chart, pass/fail checklist | Backtest DB | P1 |
| 8. Strategy Rules | All active module parameters | Rendered config, rule table, change log | Local config | P0 |
| 9. Execution Logs | Full audit trail of all system actions | Filterable log table | Log DB | P0 |

---

## 6. Architecture Plan

### Stack
| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 15 (App Router) | File-based routing, React, dark theme, localhost:3000 |
| Backend API | FastAPI (Python) | Simple REST, async, auto-docs at /docs |
| Database | SQLite (via SQLModel) | Zero-config, single file, offline-capable |
| Scheduler | APScheduler (embedded) | Runs inside FastAPI, no external broker |
| Charting | Inline SVG (Phase 1) → Lightweight Charts (Phase 2+) | No extra deps in Phase 1 |
| HTTP client | httpx (async) | Async polling of external APIs |
| Logging | Python logging → SQLite | Queryable from dashboard |
| Config | .env + python-dotenv | Keys local, never committed |
| Package mgr | uv (Python) + npm (Node) | Fast on Windows |

### Folder Structure
```
Weather1/
├── .env.example
├── .gitignore
├── README.md
├── docs/phase0_plan.md
├── data/
│   ├── weather1.db          (runtime, gitignored)
│   └── top100_wallets.json  (Phase 3)
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── scheduler.py
│   ├── models/
│   ├── routers/
│   ├── ingestion/           (Phase 2+)
│   ├── strategy/            (Phase 5+)
│   ├── risk/                (Phase 6+)
│   ├── paper_trading/       (Phase 7+)
│   └── backtest/            (Phase 6+)
└── frontend/
    ├── app/
    │   └── [9 page routes]
    └── components/
```

---

## 7. Risk Rules — $100 Paper-Trading Protocol

### A. Position Sizing
1. Default position size: $2.00 [FROM PROJECT BRIEF]
2. Elevated size $3.00: only when Module 1 + Module 2 agree AND Module 4 confirms [INFERENCE]
3. Maximum single position: $5.00 [FROM PROJECT BRIEF]
4. No averaging down on losing positions [INFERENCE]
5. Fractional sizing: $2 for uncertain signals; $3–$5 for highest-confidence only [INFERENCE]

### B. Exposure Limits
6. Max total open exposure: $35.00 [FROM PROJECT BRIEF]
7. Max open positions: 10 at $2 default [INFERENCE]
8. Max per market type: $15 global temp, $10 city-specific, $10 other [INFERENCE]
9. Max in single market: $5 [INFERENCE]

### C. Loss Limits and Stops
10. Daily soft stop at –$7.00; no new entries rest of UTC day [FROM PROJECT BRIEF]
11. Pre-warning at –$4.00 (YELLOW state) [INFERENCE]
12. Portfolio kill switch at –$15.00 (–15%); HALTED state [FROM PROJECT BRIEF]
13. Kill switch requires manual review + explicit approval to reset [INFERENCE]
14. Stop-loss per position: –15% of position value, evaluated every 15 minutes [INFERENCE]

### D. Take-Profit Rules
15. +10%: close 50% of position [FROM PROJECT BRIEF]
16. +20%: close additional 25% [FROM PROJECT BRIEF]
17. +40%: close remaining position [FROM PROJECT BRIEF]
18. Single-module signal (no Module 4): take full profit at +10% [INFERENCE]

### E. 48h Pre-Resolution Rule
19. 48h before resolution = re-evaluation checkpoint, NOT forced close [INFERENCE]
20. Questions: Has edge weakened? Is liquidity adequate? Does settlement risk outweigh upside?
21. Options: close full / reduce to 25% / hold if all favourable and risk limits respected [INFERENCE]

### F. Liquidity/Spread Rules
22. Min total liquidity: $500 [INFERENCE]
23. Max bid-ask spread: 5% of mid [INFERENCE]
24. Min resting orders: 10 [INFERENCE]
25. Entry slippage simulated: 1% [INFERENCE]
26. Exit slippage simulated: 0.5% [INFERENCE]
27. Near-resolution slippage (within 48h): additional 1.5% [INFERENCE]
28. Last trade age: skip if >6h [INFERENCE]

### G. Stale Data Rules
29. Weather data max age: 7 hours [INFERENCE]
30. NOAA anomaly: accepted up to 35 days old [INFERENCE]
31. Price data max age: 20 minutes [INFERENCE]

### H. Conflicting Data Rules
32. Require ≥2 independent sources agreement before signal [INFERENCE]
33. NWS vs Open-Meteo disagree by >10pp: downgrade to WATCH, no entry [INFERENCE]
34. NOAA partial-month vs model conflict: defer to NOAA (settlement source) [INFERENCE]

### I. Do Not Trade Conditions
35. NOAA data release due within 24h [INFERENCE]
36. Daily soft stop active [FROM PROJECT BRIEF]
37. Kill switch active [FROM PROJECT BRIEF]
38. No signal passed Module 5 liquidity filter [INFERENCE]
39. Fewer than 2 sources agree on direction [INFERENCE]
40. Market resolves within 24h and spread >3% [INFERENCE]
41. Weather data stale [INFERENCE]

### J. Risk State Labels
| State | Condition | Trading |
|---|---|---|
| GREEN | Daily loss <$4; drawdown <8%; exposure <$25 | Full |
| YELLOW | Daily loss $4–$7; or drawdown 8–12%; or exposure $25–$35 | Reduced (no >$2) |
| RED | Daily loss approaching $7; drawdown 12–14% | Exit only |
| HALTED | Daily loss ≥$7 OR drawdown ≥15% | None |

### K. Paper-to-Real Promotion Criteria (Section 7.15)
All required before Phase 10:
- ≥60 paper trades completed
- Win rate ≥52%
- Sharpe ratio >0.8
- Max paper drawdown never exceeded 12%
- Profitable in ≥3 consecutive 30-day periods
- Phase 9 security review complete
- Explicit user written approval

---

## 8. Backtesting Plan

### Acceptance Criteria (all required to proceed to Phase 7)
- Win rate ≥52% across ≥30 backtest trades
- Max drawdown <12%
- Zero kill switch triggers in primary period
- Sharpe ratio >0.8
- Module 1 alone shows ≥50% win rate
- Profitable in ≥2 of 3 sub-periods

### Failure Criteria (any one blocks paper trading)
- Win rate <48%
- Kill switch triggered >2× in any 6-month window
- Max drawdown >15%
- Total return negative after slippage
- Fewer than 30 historical signals found
- Module 2 adds zero measurable edge independently

### Fill Assumptions
- Entry: best-ask + 1% slippage
- Exit: best-bid + 0.5% slippage
- Near-resolution exit: additional 1.5% slippage
- No perfect fills

### Key Metrics
| Metric | Target |
|---|---|
| Win rate | ≥52% |
| Avg return per trade | >$0.20 on $2 size |
| Sharpe ratio | >0.8 |
| Max drawdown | <12% |
| Signal accuracy | ≥55% |

### Important Limitation
ERA5 is hindcast/reanalysis, NOT the true forecast available at time T. Module 2 backtesting with ERA5 will produce optimistic results. True archived forecast data needed. [NEEDS_CHECK]

---

## 9. Execution Roadmap

| Phase | Name | Goal | Gate Criteria |
|---|---|---|---|
| 0 | Research & Plan | Complete implementation plan | User approval of this document ✅ |
| 1 | Dashboard Skeleton | 9-page UI + FastAPI stubs | All pages load, user approves layout |
| 2 | Data Ingestion | Live Polymarket data in SQLite | 10+ markets displayed, scheduler stable 24h |
| 3 | Top Wallet Parser | Watchlist active, wallet trades visible | 5+ wallets showing live activity |
| 4 | Weather Data Connectors | All weather sources ingested | All sources green on Data Status panel |
| 5 | Signal Engine | Scored signals in Scanner | 5+ signals evaluated over 7 days, user approves quality |
| 6 | Backtesting | Historical validation | All Section 8 acceptance criteria met |
| 7 | Paper Trading $100 | Live paper P&L tracking | Section 7.15 all criteria met |
| 8 | Dry-Run Execution | Order construction only, no mainnet | Signed orders valid; Phase 9 scheduled |
| 9 | Security Review | Full audit before live | All checklist green; written user approval |
| 10 | Mainnet Pilot | First real $2 trade | Only after Phase 9 signed off |

---

## 10. Important Constraints

1. Everything inside `Weather1` folder only [FROM PROJECT BRIEF]
2. No code before Phase 1 approval [FROM PROJECT BRIEF] ✅
3. No live trading before Phase 10 approval [FROM PROJECT BRIEF]
4. No private keys before Phase 8/9 [FROM PROJECT BRIEF]
5. No real orders Phases 1–9 [FROM PROJECT BRIEF]
6. Paper trading mandatory before live [FROM PROJECT BRIEF]
7. No unaudited community repos [FROM_ATTACHED_FILES]
8. Verify official Polymarket docs before API implementation [INFERENCE]
9. CLOB V2 status verified before execution work [NEEDS_CHECK]
10. No guaranteed-profit claims [FROM PROJECT BRIEF]
11. Risk rules cannot be bypassed programmatically [FROM PROJECT BRIEF]
12. Top-wallet copying is confirmation only [INFERENCE]
13. No whale/multi-wallet replication at $100 [INFERENCE]
14. Backtest must include slippage/spread, no perfect fills [FROM PROJECT BRIEF]
15. Every phase requires explicit user approval [FROM PROJECT BRIEF]
16. `.env` and sensitive files never committed [INFERENCE]
17. Uncertainty always labelled [NEEDS_CHECK] [FROM PROJECT BRIEF]
18. System must remain explainable through logs [FROM PROJECT BRIEF]

---

## Recommended Locked Strategy v1

**Archetype:** Sharp Selector — modelled on DarbySkees (50%), MtnMark (29.1%), CoffeeLover (31.7%), bama124 (21.1%), 9985 (9.6%).

**Entry criteria (must satisfy ALL):**
- Module 1 OR Module 2 signal present (Module 1 + 2 together preferred)
- Confidence score >70% (two sources agree)
- Module 5 liquidity gate passes
- No risk limit breach (Module 6)

**Sizing:**
- $2 default (single module signal)
- $3 (two modules + Module 4 wallet confirmation)
- $5 (maximum, highest conviction only)

**Exit:**
- +10% → close 50%
- +20% → close additional 25%
- +40% → close remaining
- –15% → stop-loss full close
- 48h checkpoint → re-evaluate

**Why achievable at $100:**
- Sharp Selector pattern works at any capital scale
- All required data sources are free
- No volume or market-making infrastructure required
- Edge comes from data literacy, not capital size

---

## Open Questions / Items Needing Verification

### API / Technical [NEEDS_CHECK]
1. Current CLOB V2 base URL (last known: clob.polymarket.com)
2. Current Gamma API base URL (last known: gamma-api.polymarket.com)
3. Current Data API base URL for wallet history
4. Whether CLOB orderbook reads require authentication
5. WebSocket endpoint and auth requirements
6. Rate limits on all three APIs
7. Whether any official Polymarket testnet/sandbox exists
8. CLOB V1 sunset status

### Weather Data [NEEDS_CHECK]
9. Exact settlement data source Polymarket uses for "hottest month on record" markets
10. NOAA CDO API token requirement and current endpoint
11. Availability of true archived NWS/ECMWF forecast data (not ERA5) for Module 2 backtesting
12. minuteTemp data source availability

### Strategy / Data [NEEDS_CHECK]
13. Historical Polymarket orderbook depth data for backtest fill simulation
14. Full wallet trade history depth from Data API
15. Whether Polycool/Notion top-67 data is exportable in structured format
