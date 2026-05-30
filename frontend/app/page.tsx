"use client";
import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────
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
interface WalletSummary { total_wallets: number; watchlist_size: number; }
interface ShadowStatus {
  total_observations: number;
  active_observations: number;
  total_snapshots: number;
  calendar_days_observed: number;
  avg_directional_move_pct: number | null;
  avg_spread_pct: number | null;
  positive_moves: number;
  negative_moves: number;
  readiness_status: string;
  phase7_status: string;
  phase7_promotion_ready: boolean;
  days_until_review: number;
  obs_until_review: number;
  promotion_criteria: Record<string, { required: string | number; actual: string | number; pass: boolean }>;
  daily_summaries: Array<{ date: string; active_obs: number; snapshots: number; avg_spread_pct: number | null; avg_dir_move_pct: number | null }>;
}
interface SchedulerStatus { running: boolean; jobs: Array<{ id: string; next_run_utc: string | null }>; }

// ── Helpers ───────────────────────────────────────────────────────────────────
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
  return <span style={{ padding: "2px 8px", borderRadius: 8, fontSize: 10, fontWeight: 700, background: bg, color, border: `1px solid ${color}44` }}>{status.toUpperCase()}</span>;
}
function SourceRow({ label, status, records, lastRun, error }: { label: string; status: string; records: number; lastRun: string | null; error: string | null }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "6px 0", borderBottom: "1px solid #21262d" }}>
      <div style={{ width: 150, fontSize: 12, color: "#e6edf3", fontWeight: 600 }}>{label}</div>
      <StatusPill status={status} />
      <div style={{ fontSize: 11, color: "#8b949e", flex: 1 }}>
        {records > 0 ? `${records.toLocaleString()} records` : "no data"} · {timeAgo(lastRun)}
        {error && <span style={{ color: "#f85149", marginLeft: 6 }}>· {error.slice(0, 50)}</span>}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function OverviewPage() {
  const [ingestion, setIngestion] = useState<IngestionStatus | null>(null);
  const [weather, setWeather]     = useState<WeatherStatus | null>(null);
  const [wallets, setWallets]     = useState<WalletSummary | null>(null);
  const [shadow, setShadow]       = useState<ShadowStatus | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [backendOnline, setOnline] = useState<boolean | null>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    Promise.allSettled([
      fetch(apiUrl("/ingestion/status")).then(r => r.json()),
      fetch(apiUrl("/weather/status")).then(r => r.json()),
      fetch(apiUrl("/wallets/summary")).then(r => r.json()),
      fetch(apiUrl("/shadow/status")).then(r => r.json()),
      fetch(apiUrl("/scheduler/status")).then(r => r.json()),
    ]).then(([ing, wx, wl, sh, sch]) => {
      setOnline(ing.status === "fulfilled");
      if (ing.status === "fulfilled") setIngestion(ing.value as IngestionStatus);
      if (wx.status  === "fulfilled") setWeather(wx.value as WeatherStatus);
      if (wl.status  === "fulfilled") setWallets(wl.value as WalletSummary);
      if (sh.status  === "fulfilled") setShadow(sh.value as ShadowStatus);
      if (sch.status === "fulfilled") setScheduler(sch.value as SchedulerStatus);
    });
  }, []);

  const shadowJob = scheduler?.jobs?.find(j => j.id === "signal_and_shadow");

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>Overview</h1>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>
          Phase 6J · Live shadow monitoring · Backend: <span style={{ fontFamily: "monospace", color: "#58a6ff", fontSize: 11 }}>{API_URL}</span>
        </p>
      </div>

      {/* ── Backend offline banner ─────────────────────────────────────────── */}
      {backendOnline === false && (
        <div style={{ background: "#1a0000", border: "1px solid #f85149", borderRadius: 8, padding: "12px 16px", marginBottom: 16, fontSize: 12, color: "#f85149" }}>
          ⚠ <strong>Cannot reach Railway backend.</strong> Backend URL: <code>{API_URL}</code>
          <div style={{ marginTop: 4, color: "#8b949e" }}>Check Railway deploy status or CORS_ORIGINS setting.</div>
        </div>
      )}

      {/* ══ SHADOW MONITORING — Live ════════════════════════════════════════ */}
      <div style={{ background: "#0d1a2e", border: "2px solid #1c3d6e", borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: "#58a6ff" }}>👁 Shadow Monitoring</h2>
          <span style={{ padding: "3px 10px", borderRadius: 10, fontSize: 10, fontWeight: 800, background: "#1a0000", color: "#f85149", border: "2px solid #f85149" }}>
            {shadow?.phase7_status ?? "PHASE_7_BLOCKED"}
          </span>
          <span style={{ padding: "2px 8px", borderRadius: 8, fontSize: 10, fontWeight: 700, background: "#1c2a3e", color: "#58a6ff", border: "1px solid #388bfd" }}>
            {shadow?.readiness_status ?? "COLLECTING_SHADOW_DATA"}
          </span>
          {scheduler?.running && (
            <span style={{ padding: "2px 8px", borderRadius: 8, fontSize: 10, fontWeight: 700, background: "#1f3a1f", color: "#3fb950", border: "1px solid #2ea043" }}>
              ● Scheduler Running
            </span>
          )}
        </div>
        <div style={{ fontSize: 11, color: "#58a6ff", marginBottom: 14, background: "#0a1628", borderRadius: 6, padding: "8px 12px" }}>
          🔒 Shadow observation only — no positions, no capital, no portfolio P&L.
          Directional move = market price change after signal — NOT an investment return.
        </div>

        {/* Main stats grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px,1fr))", gap: 10, marginBottom: 16 }}>
          {[
            { label: "Observations",   value: shadow?.total_observations ?? "—",       pass: (shadow?.total_observations ?? 0) >= 30,  note: "need ≥30" },
            { label: "Calendar Days",  value: `${shadow?.calendar_days_observed ?? "—"}/7`, pass: (shadow?.calendar_days_observed ?? 0) >= 7, note: "need ≥7" },
            { label: "Snapshots",      value: shadow?.total_snapshots ?? "—",           pass: true,                                     note: "price history" },
            { label: "Avg Spread",     value: shadow?.avg_spread_pct != null ? `${shadow.avg_spread_pct.toFixed(2)}%` : "—", pass: (shadow?.avg_spread_pct ?? 99) <= 5, note: "need ≤5%" },
            { label: "Avg Dir Move",   value: shadow?.avg_directional_move_pct != null ? `${shadow.avg_directional_move_pct.toFixed(2)}%` : "—", pass: (shadow?.avg_directional_move_pct ?? -1) >= 0, note: "need ≥0%" },
            { label: "Pos/Neg Moves",  value: `${shadow?.positive_moves ?? 0}✓ / ${shadow?.negative_moves ?? 0}✗`, pass: null as unknown as boolean, note: "" },
            { label: "Days Remaining", value: shadow?.days_until_review ?? "—",         pass: false,                                    note: "until 7-day review" },
            { label: "Scheduler",      value: scheduler?.running ? "Running" : "Stopped", pass: scheduler?.running ?? false,            note: "cron active" },
          ].map(s => (
            <div key={s.label} style={{ background: "#0d1117", border: `1px solid ${s.pass === true ? "#2ea04366" : s.pass === false ? "#30363d" : "#30363d"}`, borderRadius: 8, padding: "10px 12px" }}>
              <div style={{ fontSize: 9, color: "#8b949e", textTransform: "uppercase", marginBottom: 2 }}>{s.label}</div>
              <div style={{ fontSize: 16, fontWeight: 900, color: s.pass === true ? "#3fb950" : s.pass === false ? "#58a6ff" : "#e6edf3" }}>
                {s.pass === true ? "✓ " : ""}{String(s.value)}
              </div>
              {s.note && <div style={{ fontSize: 9, color: "#8b949e", marginTop: 2 }}>{s.note}</div>}
            </div>
          ))}
        </div>

        {/* 7-day progress bar */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#8b949e", marginBottom: 4 }}>
            <span>Observation progress (day {shadow?.calendar_days_observed ?? 0} / 7)</span>
            <span>{shadow?.days_until_review != null ? `${shadow.days_until_review} days remaining` : "loading…"}</span>
          </div>
          <div style={{ height: 8, background: "#21262d", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: `${Math.min(((shadow?.calendar_days_observed ?? 0) / 7) * 100, 100)}%`, height: "100%", background: "#58a6ff", borderRadius: 4 }} />
          </div>
        </div>

        {/* Next scheduler run */}
        {shadowJob?.next_run_utc && (
          <div style={{ fontSize: 11, color: "#8b949e" }}>
            Next signal + shadow run: <span style={{ color: "#e6edf3", fontFamily: "monospace" }}>{shadowJob.next_run_utc}</span>
          </div>
        )}

        {/* Promotion criteria */}
        {shadow?.promotion_criteria && (
          <div style={{ marginTop: 14, borderTop: "1px solid #1c3d6e", paddingTop: 12 }}>
            <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase", marginBottom: 8 }}>Phase 7 Promotion Criteria</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {Object.entries(shadow.promotion_criteria).map(([key, c]) => (
                <div key={key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
                  <span style={{ color: c.pass ? "#3fb950" : "#f85149", fontWeight: 700, width: 14 }}>{c.pass ? "✓" : "✗"}</span>
                  <span style={{ color: "#8b949e", flex: 1 }}>{key.replace(/_/g, " ")}</span>
                  <span style={{ color: "#e6edf3", fontFamily: "monospace" }}>{String(c.actual)}</span>
                  <span style={{ color: "#8b949e" }}>/ need {String(c.required)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Data Pipeline Status (live) ────────────────────────────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "16px 20px", marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>
          ⚡ Data Pipeline Status — Live Railway
        </div>
        <SourceRow label="Polymarket Markets" status={ingestion?.last_status ?? "never_run"} records={ingestion?.active_weather_markets_in_db ?? 0} lastRun={ingestion?.last_run_at ?? null} error={ingestion?.last_error ?? null} />
        <SourceRow label="Top 100 Wallets"    status={(wallets?.total_wallets ?? 0) > 0 ? "ok" : "never_run"} records={wallets?.total_wallets ?? 0} lastRun={null} error={null} />
        <SourceRow label="NWS Forecasts"      status={weather?.sources?.nws?.status ?? "never_run"} records={weather?.sources?.nws?.records_stored ?? 0} lastRun={weather?.sources?.nws?.last_run ?? null} error={weather?.sources?.nws?.last_error ?? null} />
        <SourceRow label="Open-Meteo"         status={weather?.sources?.openmeteo?.status ?? "never_run"} records={weather?.sources?.openmeteo?.records_stored ?? 0} lastRun={weather?.sources?.openmeteo?.last_run ?? null} error={weather?.sources?.openmeteo?.last_error ?? null} />
        <SourceRow label="NASA GISTEMP"       status={weather?.sources?.nasa_gistemp?.status ?? "never_run"} records={weather?.sources?.nasa_gistemp?.records_stored ?? 0} lastRun={weather?.sources?.nasa_gistemp?.last_run ?? null} error={weather?.sources?.nasa_gistemp?.last_error ?? null} />
        <div style={{ display: "flex", gap: 20, marginTop: 12, paddingTop: 10, borderTop: "1px solid #21262d", flexWrap: "wrap" }}>
          {[
            { label: "Weather Markets", value: ingestion?.active_weather_markets_in_db ?? "—", color: "#58a6ff" },
            { label: "Forecast Records", value: weather?.forecast_records ?? "—", color: "#bc8cff" },
            { label: "Watchlist Wallets", value: wallets?.watchlist_size ?? "—", color: "#3fb950" },
            { label: "Real Orders", value: "Disabled", color: "#f85149" },
            { label: "Paper Trading", value: "Phase 7 Blocked", color: "#f85149" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{label}</span>
              <span style={{ fontSize: 13, fontWeight: 800, color }}>{String(value)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── MOCK section — clearly labelled ───────────────────────────────── */}
      <div style={{ background: "#1a1200", border: "2px dashed #f0883e55", borderRadius: 10, padding: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <h3 style={{ margin: 0, fontSize: 13, color: "#f0883e", textTransform: "uppercase" }}>
            Paper Portfolio Preview
          </h3>
          <span style={{ padding: "3px 10px", borderRadius: 10, fontSize: 11, fontWeight: 800, background: "#3d2b00", color: "#f0883e", border: "2px solid #f0883e" }}>
            MOCK / PLACEHOLDER — NOT LIVE
          </span>
        </div>
        <div style={{ fontSize: 12, color: "#8b949e", marginBottom: 10 }}>
          Paper trading is not active. Phase 7 is BLOCKED pending 7-day shadow monitoring + explicit approval.
          The values below are illustrative placeholders only — not real positions or real P&L.
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px,1fr))", gap: 10, opacity: 0.5 }}>
          {[
            { label: "Paper Capital (mock)", value: "$100.00", color: "#8b949e" },
            { label: "Total P&L (mock)",     value: "+$0.00",  color: "#8b949e" },
            { label: "Open Positions",        value: "0",       color: "#8b949e" },
          ].map(s => (
            <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "10px 14px" }}>
              <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: s.color }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
