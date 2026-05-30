"use client";
import { useEffect, useState } from "react";
import StatCard from "@/components/StatCard";
import MockChart from "@/components/MockChart";

const EQUITY = [
  { date: "May 10", capital: 100.00 },
  { date: "May 15", capital: 100.67 },
  { date: "May 20", capital: 101.10 },
  { date: "May 25", capital: 101.77 },
  { date: "May 30", capital: 102.04 },
];

const TOP_POSITIONS = [
  { question: "Will July 2026 be the hottest July on record?", side: "YES", entry: 0.58, current: 0.62, size: "$2.00", pnl: "+$0.14", pnlPct: "+6.9%" },
  { question: "Will 2026 be the hottest year on record globally?", side: "YES", entry: 0.68, current: 0.71, size: "$3.00", pnl: "+$0.13", pnlPct: "+4.4%" },
];

interface IngestionStatus {
  last_run_at: string | null;
  last_status: string;
  last_error: string | null;
  active_weather_markets_in_db: number;
}

interface WeatherStatus {
  stations_seeded: number;
  forecast_records: number;
  anomaly_records: number;
  sources: Record<string, { last_run: string | null; status: string; records_stored: number; last_error: string | null }>;
}

interface WalletSummary {
  total_wallets: number;
  watchlist_size: number;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "never";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  return hrs < 24 ? `${hrs}h ago` : `${Math.floor(hrs / 24)}d ago`;
}

function StatusPill({ status }: { status: string }) {
  const color = status === "ok" ? "#3fb950" : status === "never_run" ? "#8b949e" : status === "partial" ? "#d29922" : "#f85149";
  const bg    = status === "ok" ? "#1f3a1f" : status === "never_run" ? "#21262d" : status === "partial" ? "#3d2b00" : "#3d1f1f";
  return (
    <span style={{ padding: "2px 8px", borderRadius: 8, fontSize: 10, fontWeight: 700, background: bg, color, border: `1px solid ${color}44` }}>
      {status.toUpperCase()}
    </span>
  );
}

function SourceRow({ label, status, records, lastRun, error }: { label: string; status: string; records: number; lastRun: string | null; error: string | null }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "7px 0", borderBottom: "1px solid #21262d" }}>
      <div style={{ width: 140, fontSize: 12, color: "#e6edf3", fontWeight: 600 }}>{label}</div>
      <StatusPill status={status} />
      <div style={{ fontSize: 11, color: "#8b949e", flex: 1 }}>
        {records > 0 ? `${records} records` : "no data"} · {timeAgo(lastRun)}
        {error && <span style={{ color: "#f85149", marginLeft: 6 }}>· {error.slice(0, 60)}</span>}
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const [ingestion, setIngestion]       = useState<IngestionStatus | null>(null);
  const [weather, setWeather]           = useState<WeatherStatus | null>(null);
  const [wallets, setWallets]           = useState<WalletSummary | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    // Fetch all status in parallel
    Promise.allSettled([
      fetch("/api/ingestion/status").then(r => r.json()),
      fetch("/api/weather/status").then(r => r.json()),
      fetch("/api/wallets/summary").then(r => r.json()),
    ]).then(([ingRes, wxRes, wlRes]) => {
      setBackendOnline(ingRes.status === "fulfilled");
      if (ingRes.status === "fulfilled") setIngestion(ingRes.value as IngestionStatus);
      if (wxRes.status  === "fulfilled") setWeather(wxRes.value as WeatherStatus);
      if (wlRes.status  === "fulfilled") setWallets(wlRes.value as WalletSummary);
    });
  }, []);

  const marketsOk  = ingestion?.last_status === "ok";
  const walletsOk  = (wallets?.total_wallets ?? 0) > 0;
  const wxNwsOk    = weather?.sources?.nws?.status === "ok" || weather?.sources?.nws?.status === "partial";
  const wxOmOk     = weather?.sources?.openmeteo?.status === "ok";
  const wxGlbOk    = weather?.sources?.nasa_gistemp?.status === "ok";

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>Overview</h1>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>
          Phase 4 · Weather data connected · Portfolio and signals still mock
        </p>
      </div>

      {/* ── Data Status Panel ──────────────────────────────────────────────── */}
      <div style={{
        background: "#161b22", border: "1px solid #30363d",
        borderRadius: 10, padding: "16px 20px", marginBottom: 20,
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>
          ⚡ Data Pipeline Status — Phase 4
        </div>

        {backendOnline === false && (
          <div style={{ color: "#f85149", fontSize: 12, marginBottom: 10 }}>
            ⚠ Backend offline — start with: <code>cd backend && uv run uvicorn main:app --reload --port 8000</code>
          </div>
        )}

        {/* Source rows */}
        <div>
          <SourceRow
            label="Polymarket Markets"
            status={ingestion?.last_status ?? "never_run"}
            records={ingestion?.active_weather_markets_in_db ?? 0}
            lastRun={ingestion?.last_run_at ?? null}
            error={ingestion?.last_error ?? null}
          />
          <SourceRow
            label="Top 100 Wallets"
            status={walletsOk ? "ok" : "never_run"}
            records={wallets?.total_wallets ?? 0}
            lastRun={null}
            error={null}
          />
          <SourceRow
            label="NWS Forecasts"
            status={weather?.sources?.nws?.status ?? "never_run"}
            records={weather?.sources?.nws?.records_stored ?? 0}
            lastRun={weather?.sources?.nws?.last_run ?? null}
            error={weather?.sources?.nws?.last_error ?? null}
          />
          <SourceRow
            label="Open-Meteo"
            status={weather?.sources?.openmeteo?.status ?? "never_run"}
            records={weather?.sources?.openmeteo?.records_stored ?? 0}
            lastRun={weather?.sources?.openmeteo?.last_run ?? null}
            error={weather?.sources?.openmeteo?.last_error ?? null}
          />
          <SourceRow
            label="NASA GISTEMP"
            status={weather?.sources?.nasa_gistemp?.status ?? "never_run"}
            records={weather?.sources?.nasa_gistemp?.records_stored ?? 0}
            lastRun={weather?.sources?.nasa_gistemp?.last_run ?? null}
            error={weather?.sources?.nasa_gistemp?.last_error ?? null}
          />
        </div>

        {/* Quick stats row */}
        <div style={{ display: "flex", gap: 20, marginTop: 14, paddingTop: 12, borderTop: "1px solid #21262d", flexWrap: "wrap" }}>
          {[
            { label: "Weather Markets", value: ingestion?.active_weather_markets_in_db ?? "—", color: "#58a6ff" },
            { label: "Forecast Records", value: weather?.forecast_records ?? "—", color: "#bc8cff" },
            { label: "Global Anomalies", value: weather?.anomaly_records ?? "—", color: "#f0883e" },
            { label: "Watchlist Wallets", value: wallets?.watchlist_size ?? "—", color: "#3fb950" },
            { label: "Real Orders", value: "Disabled", color: "#f85149" },
            { label: "Paper Trading", value: "Not active yet", color: "#d29922" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.4px" }}>{label}</span>
              <span style={{ fontSize: 14, fontWeight: 800, color }}>{String(value)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Stat cards (portfolio — still mock) ──────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16, marginBottom: 24 }}>
        <StatCard label="Paper Capital" value="$102.04" sub="started at $100.00" color="#3fb950" />
        <StatCard label="Total P&L" value="+$2.04" sub="+2.04% (mock)" color="#3fb950" />
        <StatCard label="Today's P&L" value="+$0.27" sub="unrealised (mock)" color="#3fb950" />
        <StatCard label="Open Positions" value="2" sub="$5.00 deployed (mock)" color="#58a6ff" />
        <StatCard label="Active Signals" value="3" sub="1 enter · 2 watch (mock)" color="#f0883e" />
        <StatCard label="Risk State" value="GREEN" sub="drawdown: 0% (mock)" color="#3fb950" />
      </div>

      {/* ── Equity chart (mock) ───────────────────────────────────────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 13, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Equity Curve — All Time
          </h3>
          <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: "#3d2b00", color: "#f0883e", border: "1px solid #f0883e44" }}>MOCK</span>
        </div>
        <MockChart data={EQUITY} height={160} color="#3fb950" label="Paper Capital ($) — mock data" />
      </div>

      {/* ── Open positions (mock) ─────────────────────────────────────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 13, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Open Positions
          </h3>
          <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: "#3d2b00", color: "#f0883e", border: "1px solid #f0883e44" }}>MOCK</span>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #30363d" }}>
              {["Market", "Side", "Entry", "Current", "Size", "Unrealised P&L"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "6px 10px", fontSize: 11, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {TOP_POSITIONS.map((p, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #21262d" }}>
                <td style={{ padding: "10px 10px", fontSize: 12, color: "#e6edf3", maxWidth: 300 }}>{p.question}</td>
                <td style={{ padding: "10px 10px", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>{p.side}</td>
                <td style={{ padding: "10px 10px", fontSize: 12, color: "#8b949e", fontFamily: "monospace" }}>{p.entry}</td>
                <td style={{ padding: "10px 10px", fontSize: 12, color: "#e6edf3", fontFamily: "monospace" }}>{p.current}</td>
                <td style={{ padding: "10px 10px", fontSize: 12, color: "#58a6ff" }}>{p.size}</td>
                <td style={{ padding: "10px 10px", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>{p.pnl} ({p.pnlPct})</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
