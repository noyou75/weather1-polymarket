"use client";
import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────
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
  daily_summaries: Array<{
    date: string; active_obs: number; new: number; updated: number;
    snapshots: number; avg_spread_pct: number | null; avg_dir_move_pct: number | null;
    pos: number; neg: number;
  }>;
}
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
  last_updated_at: string;
  times_seen: number;
  initial_mid_price: number | null;
  initial_spread_pct: number | null;
  initial_liquidity: number | null;
  latest_mid_price: number | null;
  directional_move_pct: number | null;
  is_active: boolean;
}
interface ObsResponse { count: number; observations: ShadowObs[]; }

// ── Helpers ───────────────────────────────────────────────────────────────────
const CRIT_LABEL: Record<string, string> = {
  observations_30_plus:       "≥ 30 shadow observations",
  calendar_days_7_plus:       "≥ 7 calendar days observed",
  avg_spread_acceptable:      "Average spread ≤ 5%",
  directional_move_positive:  "Average directional move ≥ 0%",
  explicit_user_approval:     "Explicit written user approval",
};

// ── Page ──────────────────────────────────────────────────────────────────────
export default function ShadowPage() {
  const [status, setStatus]   = useState<ShadowStatus | null>(null);
  const [obs, setObs]         = useState<ShadowObs[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const [sRes, oRes] = await Promise.all([
        fetch(apiUrl("/shadow/status"),                      { cache: "no-store" }),
        fetch(`${apiUrl("/shadow/observations")}?limit=100`, { cache: "no-store" }),
      ]);
      if (!sRes.ok) throw new Error(`Shadow status: HTTP ${sRes.status}`);
      setStatus(await sRes.json());
      if (oRes.ok) { const d: ObsResponse = await oRes.json(); setObs(d.observations ?? []); }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const topPos = [...obs].filter(o => (o.directional_move_pct ?? 0) > 0).sort((a,b) => (b.directional_move_pct ?? 0) - (a.directional_move_pct ?? 0)).slice(0,5);
  const topNeg = [...obs].filter(o => (o.directional_move_pct ?? 0) < 0).sort((a,b) => (a.directional_move_pct ?? 0) - (b.directional_move_pct ?? 0)).slice(0,5);

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>👁 Shadow Monitoring</h1>
          <span style={{ padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800, background: "#1a0000", color: "#f85149", border: "2px solid #f85149" }}>
            {status?.phase7_status ?? "PHASE_7_BLOCKED"}
          </span>
          <span style={{ padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800, background: "#1c2a3e", color: "#58a6ff", border: "1px solid #388bfd" }}>
            {status?.readiness_status ?? "COLLECTING_SHADOW_DATA"}
          </span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 6 }}>
          Live signal observation · Collecting real entry prices for 7 calendar days · Phase 7 requires explicit approval
        </p>
      </div>

      {/* ── Safety notice ─────────────────────────────────────────────────── */}
      <div style={{ background: "#0d2818", border: "1px solid #2ea043", borderRadius: 8, padding: "10px 16px", marginBottom: 16, fontSize: 12, color: "#3fb950" }}>
        🔒 <strong>Shadow observation only.</strong>{" "}
        No positions created. No capital deployed. No portfolio P&L.
        directional_move_pct = market price move after signal — NOT an investment return.
        Phase 7 (paper trading) always requires explicit written user approval.
      </div>

      {/* ── Error ──────────────────────────────────────────────────────────── */}
      {error && (
        <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 8, padding: "14px 18px", color: "#f85149", fontSize: 13, marginBottom: 16 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && <div style={{ padding: 40, textAlign: "center", color: "#8b949e" }}>⏳ Loading shadow data…</div>}

      {!loading && status && (
        <>
          {/* ── Summary chips ──────────────────────────────────────────────── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px,1fr))", gap: 12, marginBottom: 22 }}>
            {[
              { label: "Observations",    value: `${status.total_observations}/30`, pass: status.total_observations >= 30 },
              { label: "Calendar Days",   value: `${status.calendar_days_observed}/7`, pass: status.calendar_days_observed >= 7 },
              { label: "Snapshots",       value: String(status.total_snapshots),   pass: null as unknown as boolean },
              { label: "Avg Spread",      value: status.avg_spread_pct != null ? `${status.avg_spread_pct.toFixed(2)}%` : "—", pass: (status.avg_spread_pct ?? 99) <= 5 },
              { label: "Avg Dir Move",    value: status.avg_directional_move_pct != null ? `${status.avg_directional_move_pct.toFixed(2)}%` : "—", pass: (status.avg_directional_move_pct ?? -1) >= 0 },
              { label: "Pos/Neg",         value: `${status.positive_moves}↑ ${status.negative_moves}↓`, pass: null as unknown as boolean },
              { label: "Days Remaining",  value: String(status.days_until_review), pass: false },
            ].map(s => (
              <div key={s.label} style={{ background: "#161b22", border: `1px solid ${s.pass === true ? "#2ea04366" : "#30363d"}`, borderRadius: 8, padding: "12px 14px" }}>
                <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
                <div style={{ fontSize: 18, fontWeight: 900, color: s.pass === true ? "#3fb950" : s.pass === false ? "#58a6ff" : "#e6edf3", marginTop: 2 }}>
                  {s.pass === true ? "✓ " : ""}{s.value}
                </div>
              </div>
            ))}
          </div>

          {/* ── 7-day progress bar ─────────────────────────────────────────── */}
          <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "16px 20px", marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#8b949e", marginBottom: 8 }}>
              <span>7-Day Observation Progress</span>
              <span style={{ color: status.days_until_review > 0 ? "#f0883e" : "#3fb950" }}>
                {status.days_until_review > 0 ? `${status.days_until_review} days remaining` : "✓ Complete"}
              </span>
            </div>
            <div style={{ height: 12, background: "#21262d", borderRadius: 6, overflow: "hidden", marginBottom: 12 }}>
              <div style={{ width: `${Math.min((status.calendar_days_observed / 7) * 100, 100)}%`, height: "100%", background: "#58a6ff", borderRadius: 6 }} />
            </div>
            {/* Daily summary table */}
            {status.daily_summaries.length > 0 && (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #30363d" }}>
                    {["Date", "Active Obs", "Snapshots", "Avg Spread", "Avg Dir Move"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "6px 10px", fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {status.daily_summaries.map(d => (
                    <tr key={d.date} style={{ borderBottom: "1px solid #21262d" }}>
                      <td style={{ padding: "8px 10px", fontSize: 12, fontFamily: "monospace", color: "#e6edf3" }}>{d.date}</td>
                      <td style={{ padding: "8px 10px", fontSize: 12, color: "#58a6ff" }}>{d.active_obs}</td>
                      <td style={{ padding: "8px 10px", fontSize: 12, color: "#8b949e" }}>{d.snapshots}</td>
                      <td style={{ padding: "8px 10px", fontSize: 12, color: (d.avg_spread_pct ?? 99) <= 5 ? "#3fb950" : "#f85149" }}>
                        {d.avg_spread_pct != null ? `${d.avg_spread_pct.toFixed(2)}%` : "—"}
                      </td>
                      <td style={{ padding: "8px 10px", fontSize: 12, color: (d.avg_dir_move_pct ?? 0) >= 0 ? "#3fb950" : "#f85149" }}>
                        {d.avg_dir_move_pct != null ? `${d.avg_dir_move_pct >= 0 ? "+" : ""}${d.avg_dir_move_pct.toFixed(2)}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* ── Promotion criteria ─────────────────────────────────────────── */}
          <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 20 }}>
            <h3 style={{ margin: "0 0 14px", fontSize: 12, color: "#8b949e", textTransform: "uppercase" }}>Phase 7 Promotion Criteria</h3>
            {Object.entries(status.promotion_criteria).map(([key, c]) => (
              <div key={key} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0", borderBottom: "1px solid #21262d", fontSize: 12 }}>
                <span style={{ color: c.pass ? "#3fb950" : "#f85149", fontWeight: 900, fontSize: 14, width: 16 }}>{c.pass ? "✓" : "✗"}</span>
                <span style={{ color: "#e6edf3", flex: 1 }}>{CRIT_LABEL[key] ?? key.replace(/_/g, " ")}</span>
                <span style={{ color: "#8b949e", fontFamily: "monospace" }}>actual: {String(c.actual)}</span>
                <span style={{ color: "#30363d" }}>/ need {String(c.required)}</span>
              </div>
            ))}
            <div style={{ marginTop: 12, fontSize: 11, color: "#f85149", fontWeight: 700 }}>
              Phase 7 is NEVER auto-approved. All criteria passing + explicit written approval required.
            </div>
          </div>

          {/* ── Top positive + negative moves ─────────────────────────────── */}
          {(topPos.length > 0 || topNeg.length > 0) && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
              {[
                { title: "↑ Top Positive Moves", items: topPos, color: "#3fb950" },
                { title: "↓ Top Negative Moves", items: topNeg, color: "#f85149" },
              ].map(({ title, items, color }) => (
                <div key={title} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 16 }}>
                  <div style={{ fontSize: 11, color: "#8b949e", textTransform: "uppercase", marginBottom: 10 }}>{title}</div>
                  {items.length === 0 ? <div style={{ fontSize: 12, color: "#8b949e" }}>No data yet</div> : items.map(o => (
                    <div key={o.id} style={{ padding: "6px 0", borderBottom: "1px solid #21262d", fontSize: 11 }}>
                      <div style={{ color: "#e6edf3", marginBottom: 2 }}>{o.question.slice(0, 60)}…</div>
                      <div style={{ display: "flex", gap: 12, color: "#8b949e" }}>
                        <span style={{ color, fontWeight: 700 }}>{o.directional_move_pct != null ? `${o.directional_move_pct >= 0 ? "+" : ""}${o.directional_move_pct.toFixed(2)}%` : "—"}</span>
                        <span>{o.side}</span>
                        <span>conf={o.confidence}</span>
                        <span>seen {o.times_seen}×</span>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* ── Observation table ──────────────────────────────────────────── */}
          {obs.length > 0 && (
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
              <div style={{ padding: "12px 16px", borderBottom: "1px solid #30363d", fontSize: 12, fontWeight: 700, color: "#58a6ff" }}>
                Shadow Observations ({obs.length}) — observation only, no positions
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
                      {["Market", "Type", "Side", "Mid", "Spread", "Dir Move", "Seen", "Conf", "Rec"].map(h => (
                        <th key={h} style={{ textAlign: "left", padding: "8px 10px", fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {obs.slice(0, 30).map(o => {
                      const dm = o.directional_move_pct;
                      const dmColor = dm == null ? "#8b949e" : dm > 0 ? "#3fb950" : dm < 0 ? "#f85149" : "#8b949e";
                      return (
                        <tr key={o.id} style={{ borderBottom: "1px solid #21262d" }}>
                          <td style={{ padding: "7px 10px", fontSize: 10, color: "#e6edf3", maxWidth: 200 }}>{o.question.slice(0, 55)}</td>
                          <td style={{ padding: "7px 10px", fontSize: 10, color: "#bc8cff" }}>{o.market_type.replace(/_/g, " ")}</td>
                          <td style={{ padding: "7px 10px", fontWeight: 700, fontSize: 11, color: o.side === "YES" ? "#3fb950" : o.side === "NO" ? "#f85149" : "#8b949e" }}>{o.side}</td>
                          <td style={{ padding: "7px 10px", fontSize: 11, fontFamily: "monospace" }}>{o.initial_mid_price?.toFixed(3) ?? "—"}</td>
                          <td style={{ padding: "7px 10px", fontSize: 11, color: (o.initial_spread_pct ?? 99) <= 2 ? "#3fb950" : "#d29922" }}>
                            {o.initial_spread_pct != null ? `${o.initial_spread_pct.toFixed(1)}%` : "—"}
                          </td>
                          <td style={{ padding: "7px 10px", fontSize: 11, fontWeight: 700, color: dmColor }}>
                            {dm != null ? `${dm >= 0 ? "+" : ""}${dm.toFixed(2)}%` : "—"}
                          </td>
                          <td style={{ padding: "7px 10px", fontSize: 11, color: "#8b949e" }}>{o.times_seen}×</td>
                          <td style={{ padding: "7px 10px", fontSize: 11 }}>{o.confidence}</td>
                          <td style={{ padding: "7px 10px", fontSize: 10, color: "#f0883e" }}>{o.recommendation.replace(/_/g, " ").slice(0, 20)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
