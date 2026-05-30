# Weather1 — Polymarket Weather Edge Engine

> **Phase 6F — Shadow Monitoring Active**  
> ⚠️ **PHASE 7 BLOCKED.** Shadow observation layer collecting live signal prices.  
> No real orders. No private keys. No positions. No paper trading.  
> Strategy v1.1+verified passed MEDIUM-quality backtest. 7-day shadow observation required before Phase 7 consideration.

---

## Project Goal

A professional analytics dashboard and automated paper-trading system for Polymarket weather markets.  
Long-term ambition: compete toward the Top 50 Polymarket Weather traders.

---

## Current Phase: 6F — Shadow Monitoring

**Phase 7 (paper trading) is BLOCKED.** To unblock it:
1. Collect ≥ 30 shadow observations ✅ (30 collected on Day 1)
2. Observe for ≥ 7 calendar days ⏳ (Day 1 of 7 complete)
3. Avg spread at signal time ≤ 5% ✅ (currently 1.18%)
4. Avg directional move ≥ 0% ✅ (currently 0.0% — updating)
5. Explicit written user approval ❌ (not yet given)

---

## Railway Cloud Deployment (Phase 6G) — Recommended for 7-Day Shadow Monitoring

Deploy the backend to Railway so shadow monitoring runs continuously without your PC staying on.

### Prerequisites
- [Railway account](https://railway.app) (free tier is sufficient)
- Railway CLI: `npm install -g @railway/cli` (optional — GUI works too)
- Your `Weather1` repo pushed to GitHub

### Step-by-step Railway Deployment

**1. Create a new Railway project**
- Go to [railway.app/new](https://railway.app/new)
- Choose "Deploy from GitHub repo"
- Select your `Weather1` repository

**2. Configure the service**
In Railway → your service → Settings:
- **Root Directory**: `backend`
- **Start Command**: `uv run uvicorn main:app --host 0.0.0.0 --port $PORT`
- (Railway sets `$PORT` automatically)

**3. Add a persistent Volume**
In Railway → your service → Volumes → Add Volume:
- **Mount path**: `/data`
- This is where the SQLite database lives between restarts

**4. Set environment variables**
In Railway → your service → Variables → Add all from below:

```
WEATHER1_DB_PATH=/data/weather1.db
SCHEDULER_ENABLED=true
APP_ENV=production
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

See `backend/.env.railway.example` for the full template.  
⚠️ Never add `WALLET_PRIVATE_KEY` or any order-related keys.

**5. Deploy**
Railway auto-deploys on GitHub push. Or click "Deploy" in the GUI.

**6. Verify it's running**
```
https://your-service.railway.app/health
  → {"status":"ok","db":"ok","scheduler":true,"phase":"6G"}

https://your-service.railway.app/shadow/status
  → {"total_observations":30,"phase7_status":"PHASE_7_BLOCKED",...}

https://your-service.railway.app/shadow/readiness
  → {"phase7_status":"PHASE_7_BLOCKED","calendar_days_observed":1,...}
```

**7. Check daily progress**
```
https://your-service.railway.app/shadow/daily
  → daily summary table with one row per observation day
```

**8. Seed initial data after first deploy**
On first deploy the database is empty. Trigger ingestion manually:
```bash
# Seed wallets
curl -X POST https://your-service.railway.app/wallets/import-top100

# Seed weather stations + run ingestion
curl -X POST https://your-service.railway.app/ingestion/run-once

# Verify settlement sources
curl -X POST https://your-service.railway.app/settlement/verify-now

# Run first shadow observation
curl -X POST https://your-service.railway.app/shadow/run-once
```
After the first manual seed, the scheduler handles everything automatically.

> ⚠️ **Note**: If you redeploy without a Volume, the database resets.  
> Always attach the persistent Volume before first deploy.

---

## How to Keep Shadow Monitoring Running (Next 7 Days)

### Step 1 — Start the backend (keep running)
```bash
cd Weather1\backend
uv run uvicorn main:app --reload --port 8000
```

The scheduler runs automatically:
- Every **5 minutes**: Polymarket market data refresh
- Every **15 minutes**: Signal evaluation + shadow observation cycle
- Every **6 hours**: NWS/Open-Meteo weather forecasts
- Every **6 hours**: NASA GISTEMP global anomaly data

> ⚠️ **WARNING**: If you close the backend, scheduled observation stops.
> Shadow observations only accumulate while the backend is running.
> Leave it running in the background each day for the 7-day period.

### Step 2 — Start the frontend (optional, for monitoring)
```bash
cd Weather1\frontend
npm run dev
```
Open: http://localhost:3000 → Signal Scanner → Shadow Observations panel

### Step 3 — Manual observation (optional)
If you want to trigger an immediate observation cycle:
```bash
curl -X POST http://localhost:8000/shadow/run-once
```
Or from the browser: POST http://localhost:8000/docs → `/shadow/run-once`

### Step 4 — Check readiness
```bash
curl http://localhost:8000/shadow/readiness
curl http://localhost:8000/shadow/status
curl http://localhost:8000/shadow/daily
```

---

## Quick Start

### Backend (FastAPI)
```bash
cd backend
uv sync                                          # install dependencies (first time only)
uv run uvicorn main:app --reload --port 8000    # start server
```
API docs: http://localhost:8000/docs

### Frontend (Next.js)
```bash
cd frontend
npm install                                      # first time only
npm run dev
```
Dashboard: http://localhost:3000

---

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 0 | Research & Plan | ✅ Complete |
| 1 | Dashboard Skeleton | ✅ Complete |
| 2 | Data Ingestion (Polymarket) | ✅ Complete |
| 3 | Top Wallet Parser | ✅ Complete |
| 4 | Weather Data Connectors | ✅ Complete |
| 5 | Signal Engine (v1.1) | ✅ Complete |
| 6 | Backtesting | ✅ Complete (MEDIUM quality, v1.1+verified) |
| 6B | Backtest Diagnosis | ✅ Complete |
| 6C | Strategy v1.1 Calibration | ✅ Complete |
| 6D | Settlement Verification | ✅ Complete (NASA GISTEMP confirmed) |
| 6E | Shadow Observation Layer | ✅ Complete |
| **6F** | **Shadow Monitoring Hardening** | **🔄 Active — Day 1/7** |
| 7 | Paper Trading ($100) | 🚫 BLOCKED — awaiting 7-day shadow + approval |
| 8 | Dry-Run Execution | ⏳ Pending |
| 9 | Security Review | ⏳ Pending |
| 10 | Mainnet Pilot (approval required) | ⏳ Pending |

---

## Strategy v1.1 Summary

- **Type**: Sharp Selector — annual temperature rank markets (hottest year on record)
- **Settlement source**: VERIFIED — NASA GISTEMP v4 (Global Land-Ocean Temperature Index)
- **Gap threshold**: WATCH ≥ 10pp · ENTER ≥ 15pp (requires settlement verification)
- **Disabled**: Rank-2+ annual markets (0% win rate in backtest)
- **Backtest result**: 71.4% win rate · Sharpe 5.40 · Max drawdown 1.47% (MEDIUM quality)
- **Phase 7 gate**: 7-day live shadow observation + explicit user approval

---

## Risk Rules (Paper Trading — NOT YET ACTIVE)

- Starting capital: $100 (paper only)
- Default position: $2 | Max position: $5
- Max open exposure: $35
- Daily soft stop: −$7 (7%)
- Portfolio kill switch: −$15 (15%)
- Take-profit: +10% / +20% / +40%

---

## Important

- No real orders before Phase 10
- No private keys before Phase 8/9
- All phases require explicit user approval before proceeding
- See `docs/phase0_plan.md` for full implementation plan
- See `docs/phase6b_diagnosis.md` for backtest diagnosis
