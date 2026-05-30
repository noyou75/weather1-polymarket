"use client";
import { useEffect, useState } from "react";

// ── Shadow observation types ──────────────────────────────────────────────────
interface ShadowObs {
  id: number;
  market_id: string;
  question: string;
  market_type: string;
  side: string;
  recommendation: string;
  confidence: number;
  gap_pp: number | null;
  settlement_source: string;
  first_seen_at: string;
  last_updated_at: string | null;
  initial_mid_price: number | null;
  initial_spread: number | null;
  initial_liquidity: number | null;
  latest_mid_price: number | null;
  directional_move_pct: number | null;
  times_seen: number;
  is_active: boolean;
}

interface ShadowStatus {
  total_observations: number;
  active_observations: number;
  total_snapshots: number;
  calendar_days_observed: number;
  days_observed?: number;           // legacy alias
  avg_directional_move_pct: number | null;
  avg_spread_pct: number | null;
  positive_moves: number;
  negative_moves: number;
  readiness_status: string;         // COLLECTING_SHADOW_DATA | READY_FOR_REVIEW
  phase7_status: string;            // always PHASE_7_BLOCKED
  phase7_promotion_ready: boolean;
  days_until_review: number;
  obs_until_review: number;
  promotion_criteria: Record<string, { required: string | number; actual: string | number; pass: boolean }>;
  daily_summaries: Array<{
    date: string; active_obs: number; new: number; updated: number;
    snapshots: number; avg_spread_pct: number | null; avg_dir_move_pct: number | null;
    pos: number; neg: number;
  }>;
}

// ── Types ─────────────────────────────────────────────────────────────────────
interface SignalRecord {
  id: number;
  market_id: string;
  question: string;
  event_title: string | null;
  market_type: string;
  side: string;
  market_implied_prob: number | null;
  model_estimated_prob: number | null;
  probability_gap_pp: number | null;
  confidence_score: number;
  module1: string;
  module2: string;
  module4: string;
  liquidity_ok: boolean;
  settlement_verified: boolean;
  recommendation: string;
  explanation: string | null;
  created_at: string;
}

interface SignalSummary {
  run_at: string | null;
  status: string;
  evaluated: number;
  enter_candidates: number;
  watch: number;
  skip: number;
  by_recommendation: Record<string, number>;
  duration_ms: number;
}

interface SignalsResponse {
  count: number;
  run_at: string | null;
  run_status: string;
  signals: SignalRecord[];
}

// ── Colours / labels ──────────────────────────────────────────────────────────
const REC_COLOR: Record<string, string> = {
  ENTER_CANDIDATE:                 "#3fb950",
  NEEDS_SETTLEMENT_SOURCE_CHECK:   "#f0883e",
  WATCH:                           "#58a6ff",
  NEEDS_MORE_DATA:                 "#8b949e",
  SKIP_UNSUPPORTED_TYPE:           "#30363d",
  SKIP_LOW_LIQUIDITY:              "#30363d",
  SKIP_WIDE_SPREAD:                "#30363d",
  SKIP_ALREADY_RESOLVED:           "#30363d",
  SKIP_STALE_DATA:                 "#30363d",
};
const REC_BG: Record<string, string> = {
  ENTER_CANDIDATE:                 "#1f3a1f",
  NEEDS_SETTLEMENT_SOURCE_CHECK:   "#3d2b00",
  WATCH:                           "#1c2a3e",
  NEEDS_MORE_DATA:                 "#21262d",
};

const TYPE_LABEL: Record<string, string> = {
  annual_temp:         "🌡 Annual Temp Rank",
  global_monthly_temp: "🌍 Global Monthly Anomaly",
  city_station_temp:   "🏙 City Station Temp",
  hurricane:           "🌀 Hurricane",
  tornado:             "🌪 Tornado",
  earthquake:          "🔴 Earthquake",
  arctic_ice:          "🧊 Arctic Ice",
  precipitation:       "🌧 Precipitation",
  disease:             "🦠 Disease",
  excluded:            "— Other",
};

function RecBadge({ rec }: { rec: string }) {
  const color = REC_COLOR[rec] ?? "#8b949e";
  const bg    = REC_BG[rec]    ?? "#21262d";
  const label = rec.replace(/_/g, " ");
  const isSkip = rec.startsWith("SKIP");
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 8, fontSize: 10, fontWeight: 700,
      background: bg, color,
      border: `1px solid ${color}${isSkip ? "33" : "66"}`,
      opacity: isSkip ? 0.6 : 1,
    }}>{label}</span>
  );
}

function ConfBar({ score }: { score: number }) {
  const color = score >= 55 ? "#3fb950" : score >= 35 ? "#f0883e" : "#8b949e";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ width: 50, height: 6, background: "#30363d", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 11, fontWeight: 700, color }}>{score}</span>
    </div>
  );
}

function ProbCell({ prob }: { prob: number | null }) {
  if (prob == null) return <span style={{ color: "#8b949e" }}>—</span>;
  return <span style={{ fontFamily: "monospace", fontSize: 12 }}>{(prob * 100).toFixed(1)}%</span>;
}

function GapCell({ gap }: { gap: number | null }) {
  if (gap == null) return <span style={{ color: "#8b949e" }}>—</span>;
  const color = gap >= 8 ? "#3fb950" : gap <= -8 ? "#f85149" : "#d29922";
  return <span style={{ color, fontWeight: 700, fontFamily: "monospace", fontSize: 12 }}>{gap > 0 ? "+" : ""}{gap.toFixed(1)}pp</span>;
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function SignalsPage() {
  const [signals, setSignals]   = useState<SignalRecord[]>([]);
  const [summary, setSummary]   = useState<SignalSummary | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [shadowStatus, setShadowStatus] = useState<ShadowStatus | null>(null);
  const [shadowObs, setShadowObs]       = useState<ShadowObs[]>([]);

  // Filters
  const [recFilter, setRecFilter]       = useState("");
  const [typeFilter, setTypeFilter]     = useState("");
  const [minConf, setMinConf]           = useState(0);
  const [liqFilter, setLiqFilter]       = useState<"" | "true" | "false">("");
  const [search, setSearch]             = useState("");

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams({ limit: "500", min_confidence: String(minConf) });
      if (recFilter)  params.set("recommendation", recFilter);
      if (typeFilter) params.set("market_type", typeFilter);
      if (liqFilter)  params.set("liquidity_ok", liqFilter);

      const [sRes, sumRes, shStatusRes, shObsRes] = await Promise.all([
        fetch(`/api/signals/latest?${params}`, { cache: "no-store" }),
        fetch("/api/signals/summary",           { cache: "no-store" }),
        fetch("/api/shadow/status",             { cache: "no-store" }),
        fetch("/api/shadow/observations?limit=50", { cache: "no-store" }),
      ]);
      if (!sRes.ok) throw new Error(`Signals API: HTTP ${sRes.status}`);
      const sData: SignalsResponse = await sRes.json();
      setSignals(sData.signals);
      if (sumRes.ok) setSummary(await sumRes.json());
      if (shStatusRes.ok) setShadowStatus(await shStatusRes.json());
      if (shObsRes.ok) {
        const shData = await shObsRes.json();
        setShadowObs(shData.observations ?? []);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [recFilter, typeFilter, minConf, liqFilter]); // eslint-disable-line

  const visible = signals.filter(s => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.question.toLowerCase().includes(q) || (s.event_title ?? "").toLowerCase().includes(q);
  });

  const dist = summary?.by_recommendation ?? {};
  const actionable = (dist["ENTER_CANDIDATE"] ?? 0) + (dist["NEEDS_SETTLEMENT_SOURCE_CHECK"] ?? 0);

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>📡 Signal Scanner</h1>
          <span style={{ padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
            background: "#1f3a1f", color: "#3fb950", border: "1px solid #2ea043" }}>
            Phase 5 — Analytical Signals
          </span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 6 }}>
          {summary?.run_at
            ? `Last run: ${summary.run_at.slice(0, 19).replace("T", " ")} UTC · ${summary.evaluated?.toLocaleString()} markets evaluated · ${summary.duration_ms}ms`
            : "Connecting to signal engine…"}
        </p>
      </div>

      {/* ── Safety banners ─────────────────────────────────────────────────── */}
      <div style={{ background: "#0d2818", border: "1px solid #2ea043", borderRadius: 8,
        padding: "10px 16px", marginBottom: 10, fontSize: 12, color: "#3fb950" }}>
        🔒 <strong>Signals are analytical only.</strong> No real orders. No paper trading yet.
        No portfolio updates. Settlement source must be verified before any trading use.
      </div>
      <div style={{ background: "#3d2b00", border: "1px solid #f0883e44", borderRadius: 8,
        padding: "10px 16px", marginBottom: 18, fontSize: 12, color: "#f0883e" }}>
        ⚠ <strong>Settlement source not verified</strong> for any signal in Phase 5.
        All high-confidence signals are capped at 60/100 and labelled NEEDS_SETTLEMENT_SOURCE_CHECK.
        Verify the exact Polymarket resolution source before using for any real analysis.
      </div>

      {/* ── Error ──────────────────────────────────────────────────────────── */}
      {error && (
        <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 8,
          padding: "14px 18px", color: "#f85149", fontSize: 13, marginBottom: 16 }}>
          <strong>Backend error:</strong> {error}
          <div style={{ marginTop: 6, color: "#8b949e", fontSize: 11 }}>
            Run backend then: <code>POST /api/signals/run-once</code>
          </div>
        </div>
      )}

      {/* ── Summary chips ──────────────────────────────────────────────────── */}
      {summary && (
        <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
          {[
            { label: "Markets Evaluated", value: (summary.evaluated ?? 0).toLocaleString(), color: "#58a6ff" },
            { label: "Actionable (Check)", value: String(actionable),  color: "#f0883e" },
            { label: "Watch",              value: String(summary.watch ?? 0), color: "#58a6ff" },
            { label: "Skip",               value: String(summary.skip ?? 0),  color: "#8b949e" },
            { label: "Showing",            value: String(visible.length),     color: "#e6edf3" },
          ].map(s => (
            <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "10px 14px" }}>
              <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: s.color }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Distribution bar ───────────────────────────────────────────────── */}
      {Object.keys(dist).length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10,
          padding: "14px 20px", marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>
            Signal Distribution (latest run)
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {Object.entries(dist).sort(([,a],[,b]) => b-a).map(([rec, cnt]) => (
              <div key={rec} style={{ display: "flex", alignItems: "center", gap: 6,
                background: "#0d1117", border: "1px solid #30363d", borderRadius: 6, padding: "6px 10px" }}>
                <RecBadge rec={rec} />
                <span style={{ fontSize: 13, fontWeight: 800, color: REC_COLOR[rec] ?? "#8b949e" }}>{cnt}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Filters ────────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14, flexWrap: "wrap", alignItems: "center" }}>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search question…"
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3",
            padding: "6px 12px", borderRadius: 6, fontSize: 13, width: 230 }} />

        <select value={recFilter} onChange={e => setRecFilter(e.target.value)}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3",
            padding: "6px 10px", borderRadius: 6, fontSize: 13 }}>
          <option value="">All recommendations</option>
          <option value="NEEDS_SETTLEMENT_SOURCE_CHECK">Needs Check</option>
          <option value="WATCH">Watch</option>
          <option value="NEEDS_MORE_DATA">Needs More Data</option>
          <option value="SKIP_UNSUPPORTED_TYPE">Skip — Type</option>
          <option value="SKIP_LOW_LIQUIDITY">Skip — Liquidity</option>
          <option value="SKIP_WIDE_SPREAD">Skip — Spread</option>
          <option value="SKIP_ALREADY_RESOLVED">Skip — Resolved</option>
        </select>

        <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3",
            padding: "6px 10px", borderRadius: 6, fontSize: 13 }}>
          <option value="">All market types</option>
          <option value="annual_temp">Annual Temp Rank</option>
          <option value="global_monthly_temp">Global Monthly Anomaly</option>
          <option value="city_station_temp">City Station Temp</option>
        </select>

        <select value={String(minConf)} onChange={e => setMinConf(Number(e.target.value))}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3",
            padding: "6px 10px", borderRadius: 6, fontSize: 13 }}>
          <option value="0">All confidence</option>
          <option value="30">≥ 30</option>
          <option value="45">≥ 45</option>
          <option value="55">≥ 55</option>
        </select>

        <select value={liqFilter} onChange={e => setLiqFilter(e.target.value as "" | "true" | "false")}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3",
            padding: "6px 10px", borderRadius: 6, fontSize: 13 }}>
          <option value="">All liquidity</option>
          <option value="true">Liquidity OK only</option>
          <option value="false">Liquidity failures</option>
        </select>

        <button onClick={load}
          style={{ background: "#1c2a3e", border: "1px solid #388bfd", color: "#58a6ff",
            padding: "6px 14px", borderRadius: 6, fontSize: 13, cursor: "pointer" }}>
          ↻ Refresh
        </button>
        <span style={{ fontSize: 11, color: "#8b949e" }}>Showing {visible.length} signals</span>
      </div>

      {/* ── Loading ─────────────────────────────────────────────────────────── */}
      {loading && (
        <div style={{ padding: 40, textAlign: "center", color: "#8b949e" }}>⏳ Loading signals…</div>
      )}

      {/* ── Signal table ───────────────────────────────────────────────────── */}
      {!loading && !error && visible.length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
                {["Market", "Type", "Side", "Mkt %", "Model %", "Gap", "Conf", "M4", "Liq", "Recommendation"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "9px 10px", fontSize: 10,
                    color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.3px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map(s => {
                const isActionable = s.recommendation === "ENTER_CANDIDATE" || s.recommendation === "NEEDS_SETTLEMENT_SOURCE_CHECK";
                return (
                  <tr key={s.id} style={{
                    borderBottom: "1px solid #21262d",
                    background: isActionable ? "#1a1200" : "transparent",
                  }}>
                    {/* Market question */}
                    <td style={{ padding: "9px 10px", maxWidth: 260 }}>
                      <div style={{ fontSize: 11, color: "#e6edf3", lineHeight: 1.4 }}>{s.question.slice(0, 90)}</div>
                      {s.event_title && (
                        <div style={{ fontSize: 10, color: "#8b949e", marginTop: 2 }}>{s.event_title.slice(0, 50)}</div>
                      )}
                    </td>
                    {/* Type */}
                    <td style={{ padding: "9px 10px", fontSize: 10, color: "#bc8cff", whiteSpace: "nowrap" }}>
                      {TYPE_LABEL[s.market_type] ?? s.market_type}
                    </td>
                    {/* Side */}
                    <td style={{ padding: "9px 10px" }}>
                      <span style={{
                        fontWeight: 800, fontSize: 12,
                        color: s.side === "YES" ? "#3fb950" : s.side === "NO" ? "#f85149" : "#8b949e",
                      }}>{s.side}</span>
                    </td>
                    {/* Probabilities */}
                    <td style={{ padding: "9px 10px" }}><ProbCell prob={s.market_implied_prob} /></td>
                    <td style={{ padding: "9px 10px" }}><ProbCell prob={s.model_estimated_prob} /></td>
                    <td style={{ padding: "9px 10px" }}><GapCell gap={s.probability_gap_pp} /></td>
                    {/* Confidence */}
                    <td style={{ padding: "9px 10px" }}><ConfBar score={s.confidence_score} /></td>
                    {/* Module 4 */}
                    <td style={{ padding: "9px 10px", fontSize: 10 }}>
                      {s.module4 === "confirmed"
                        ? <span style={{ color: "#3fb950" }}>✓</span>
                        : <span style={{ color: "#30363d" }}>—</span>}
                    </td>
                    {/* Liquidity */}
                    <td style={{ padding: "9px 10px", fontSize: 10 }}>
                      {s.liquidity_ok
                        ? <span style={{ color: "#3fb950" }}>✓</span>
                        : <span style={{ color: "#f85149" }}>✗</span>}
                    </td>
                    {/* Recommendation */}
                    <td style={{ padding: "9px 10px" }}><RecBadge rec={s.recommendation} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && visible.length === 0 && (
        <div style={{ padding: 40, textAlign: "center", color: "#8b949e", background: "#161b22",
          borderRadius: 10, border: "1px solid #30363d" }}>
          No signals match current filters.
        </div>
      )}

      {/* ── Shadow Observation Panel (Phase 6F hardened) ───────────────────── */}
      <div style={{ background: "#0d1a2e", border: "1px solid #1c3d6e", borderRadius: 10, padding: 20, marginTop: 24, marginBottom: 4 }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
          <div style={{ fontSize: 15, fontWeight: 800, color: "#58a6ff" }}>👁 Shadow Signal Observations</div>
          <span style={{ padding: "2px 10px", borderRadius: 10, fontSize: 10, fontWeight: 800,
            background: "#1a0000", color: "#f85149", border: "2px solid #f85149" }}>
            {shadowStatus ? (shadowStatus as ShadowStatus & {phase7_status?: string}).phase7_status ?? "PHASE_7_BLOCKED" : "PHASE_7_BLOCKED"}
          </span>
          <span style={{ padding: "2px 10px", borderRadius: 10, fontSize: 10, fontWeight: 800,
            background: "#1c2a3e", color: "#58a6ff", border: "1px solid #388bfd" }}>
            Phase 6F · Not Paper Trading
          </span>
        </div>

        {/* Safety note */}
        <div style={{ background: "#0d2818", border: "1px solid #2ea04366", borderRadius: 6,
          padding: "8px 14px", marginBottom: 14, fontSize: 11, color: "#3fb950" }}>
          🔒 <strong>Shadow observation only.</strong> No positions. No capital. No portfolio P&L.
          Collecting real live prices for 7 calendar days before Phase 7 can be considered.
          directional_move_pct = market movement after signal — NOT portfolio return.
        </div>

        {/* Progress chips */}
        {shadowStatus && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(145px,1fr))", gap: 10, marginBottom: 14 }}>
              {[
                {
                  label: "Observations",
                  value: `${shadowStatus.total_observations}/30`,
                  sub: shadowStatus.obs_until_review > 0 ? `need ${shadowStatus.obs_until_review} more` : "✓ met",
                  pass: (shadowStatus.total_observations ?? 0) >= 30,
                },
                {
                  label: "Calendar Days",
                  value: `${shadowStatus.calendar_days_observed}/7`,
                  sub: shadowStatus.days_until_review > 0 ? `${shadowStatus.days_until_review} days to go` : "✓ met",
                  pass: (shadowStatus.calendar_days_observed ?? 0) >= 7,
                },
                {
                  label: "Avg Spread",
                  value: shadowStatus.avg_spread_pct != null ? `${shadowStatus.avg_spread_pct.toFixed(2)}%` : "—",
                  sub: "need ≤ 5%",
                  pass: (shadowStatus.avg_spread_pct ?? 99) <= 5,
                },
                {
                  label: "Dir Move Avg",
                  value: shadowStatus.avg_directional_move_pct != null ? `${shadowStatus.avg_directional_move_pct.toFixed(2)}%` : "—",
                  sub: "need ≥ 0%",
                  pass: (shadowStatus.avg_directional_move_pct ?? -1) >= 0,
                },
                {
                  label: "User Approval",
                  value: "Pending",
                  sub: "written required",
                  pass: false,
                },
              ].map(c => (
                <div key={c.label} style={{
                  background: "#0d1117", border: `1px solid ${c.pass ? "#2ea04366" : "#30363d"}`,
                  borderRadius: 8, padding: "10px 12px",
                }}>
                  <div style={{ fontSize: 9, color: "#8b949e", textTransform: "uppercase" }}>{c.label}</div>
                  <div style={{ fontSize: 17, fontWeight: 900, color: c.pass ? "#3fb950" : "#58a6ff", marginTop: 2 }}>
                    {c.pass ? "✓ " : ""}{c.value}
                  </div>
                  <div style={{ fontSize: 10, color: "#8b949e" }}>{c.sub}</div>
                </div>
              ))}
            </div>

            {/* 7-day progress bar */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#8b949e", marginBottom: 4 }}>
                <span>Observation progress (day {shadowStatus.calendar_days_observed}/7)</span>
                <span>{shadowStatus.calendar_days_observed >= 7 ? "✓ Complete" : `${shadowStatus.days_until_review} days remaining`}</span>
              </div>
              <div style={{ height: 8, background: "#21262d", borderRadius: 4, overflow: "hidden" }}>
                <div style={{
                  width: `${Math.min((shadowStatus.calendar_days_observed / 7) * 100, 100)}%`,
                  height: "100%",
                  background: shadowStatus.calendar_days_observed >= 7 ? "#3fb950" : "#58a6ff",
                  borderRadius: 4,
                  transition: "width 0.5s",
                }} />
              </div>
            </div>
          </>
        )}
        {shadowObs.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #1c3d6e", background: "#0a1628" }}>
                  {["Question", "Side", "Live Mid", "Spread", "Liq", "Dir Move ▲", "Seen"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "7px 10px", fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shadowObs.slice(0, 15).map(o => {
                  const dm = o.directional_move_pct;
                  const dmColor = dm == null ? "#8b949e" : dm > 0 ? "#3fb950" : dm < 0 ? "#f85149" : "#8b949e";
                  return (
                    <tr key={o.id} style={{ borderBottom: "1px solid #1a2744" }}>
                      <td style={{ padding: "7px 10px", fontSize: 10, color: "#e6edf3", maxWidth: 240 }}>{o.question.slice(0, 72)}</td>
                      <td style={{ padding: "7px 10px", fontWeight: 700, fontSize: 11,
                        color: o.side === "YES" ? "#3fb950" : o.side === "NO" ? "#f85149" : "#8b949e" }}>{o.side}</td>
                      <td style={{ padding: "7px 10px", fontSize: 11, fontFamily: "monospace" }}>{o.initial_mid_price?.toFixed(4) ?? "—"}</td>
                      <td style={{ padding: "7px 10px", fontSize: 11,
                        color: (o.initial_spread ?? 0) <= 0.02 ? "#3fb950" : "#d29922" }}>
                        {o.initial_spread != null ? `${(o.initial_spread*100).toFixed(1)}%` : "—"}</td>
                      <td style={{ padding: "7px 10px", fontSize: 11, color: "#58a6ff" }}>
                        {o.initial_liquidity != null ? `$${(o.initial_liquidity/1000).toFixed(1)}K` : "—"}</td>
                      <td style={{ padding: "7px 10px", fontSize: 11, fontWeight: 700, color: dmColor }}>
                        {dm != null ? `${dm >= 0 ? "+" : ""}${dm.toFixed(2)}%` : "—"}</td>
                      <td style={{ padding: "7px 10px", fontSize: 11, color: "#8b949e" }}>{o.times_seen}×</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {shadowObs.length > 15 && (
              <div style={{ padding: "8px 10px", fontSize: 11, color: "#8b949e" }}>Showing 15 of {shadowObs.length}</div>
            )}
          </div>
        ) : (
          <div style={{ color: "#8b949e", fontSize: 12 }}>No shadow observations yet — run POST /api/shadow/run-once after signal evaluation.</div>
        )}

        {/* Daily summary table */}
        {shadowStatus && shadowStatus.daily_summaries && shadowStatus.daily_summaries.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 11, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
              Daily Observation History
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #1c3d6e", background: "#0a1628" }}>
                  {["Date", "Active Obs", "Snapshots", "Avg Spread", "Avg Dir Move", "+ Moves", "− Moves"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "6px 10px", fontSize: 10, color: "#8b949e" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shadowStatus.daily_summaries.map(d => (
                  <tr key={d.date} style={{ borderBottom: "1px solid #1a2744" }}>
                    <td style={{ padding: "6px 10px", color: "#e6edf3", fontFamily: "monospace" }}>{d.date}</td>
                    <td style={{ padding: "6px 10px", color: "#58a6ff" }}>{d.active_obs}</td>
                    <td style={{ padding: "6px 10px", color: "#8b949e" }}>{d.snapshots}</td>
                    <td style={{ padding: "6px 10px", color: d.avg_spread_pct != null && d.avg_spread_pct <= 5 ? "#3fb950" : "#d29922" }}>
                      {d.avg_spread_pct != null ? `${d.avg_spread_pct.toFixed(2)}%` : "—"}
                    </td>
                    <td style={{ padding: "6px 10px", fontWeight: 700,
                      color: d.avg_dir_move_pct == null ? "#8b949e" : d.avg_dir_move_pct >= 0 ? "#3fb950" : "#f85149" }}>
                      {d.avg_dir_move_pct != null ? `${d.avg_dir_move_pct >= 0 ? "+" : ""}${d.avg_dir_move_pct.toFixed(2)}%` : "—"}
                    </td>
                    <td style={{ padding: "6px 10px", color: "#3fb950" }}>{d.pos}</td>
                    <td style={{ padding: "6px 10px", color: "#f85149" }}>{d.neg}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <div style={{ marginTop: 16, fontSize: 11, color: "#8b949e", lineHeight: 1.6 }}>
        <strong style={{ color: "#30363d" }}>Phase 6 notes:</strong>{" "}
        Annual/monthly temp markets: settlement VERIFIED (NASA GISTEMP v4).
        City markets: settlement unverified (NWS ≠ Polymarket source).
        NEEDS_SETTLEMENT_SOURCE_CHECK = gap detected, requires further verification before use.{" "}
        Module 4 (wallet confirmation) uses static May 2026 Top 100 snapshot.{" "}
        No trades. No paper portfolio. No real orders.
      </div>
    </div>
  );
}
