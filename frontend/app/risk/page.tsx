"use client";
import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

interface ShadowStatus {
  total_observations: number;
  calendar_days_observed: number;
  avg_spread_pct: number | null;
  avg_directional_move_pct: number | null;
  phase7_status: string;
  days_until_review: number;
  obs_until_review: number;
  promotion_criteria: Record<string, { pass: boolean; actual: string | number; required: string | number }>;
}

const CRIT_LABEL: Record<string, string> = {
  observations_30_plus:      "≥ 30 shadow observations",
  calendar_days_7_plus:      "≥ 7 calendar days observed",
  avg_spread_acceptable:     "Average spread ≤ 5%",
  directional_move_positive: "Avg directional move ≥ 0%",
  explicit_user_approval:    "Explicit written user approval",
};

const PHASE0_RISK_RULES = [
  { rule: "Portfolio max drawdown",  value: "15% (−$15 on $100)", icon: "🛡" },
  { rule: "Daily soft stop",         value: "7% (−$7/day)",       icon: "⏸" },
  { rule: "Default position size",   value: "$2.00",              icon: "📏" },
  { rule: "Maximum position",        value: "$5.00",              icon: "📏" },
  { rule: "Max open exposure",       value: "$35.00",             icon: "📊" },
  { rule: "Stop-loss per trade",     value: "−15% per position",  icon: "🔴" },
  { rule: "Take-profit tier 1",      value: "+10% → close 50%",   icon: "🟢" },
  { rule: "Take-profit tier 2",      value: "+20% → close 25%",   icon: "🟢" },
  { rule: "Take-profit tier 3",      value: "+40% → close all",   icon: "🟢" },
  { rule: "48h pre-resolution",      value: "Re-evaluate (not forced close)", icon: "⏱" },
  { rule: "Real orders",             value: "DISABLED",           icon: "🚫" },
  { rule: "Paper trading",           value: "Phase 7 BLOCKED",    icon: "🚫" },
];

export default function RiskPage() {
  const [shadow, setShadow]   = useState<ShadowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    fetch(apiUrl("/shadow/status"), { cache: "no-store" })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d => setShadow(d as ShadowStatus))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>🛡 Risk Monitor</h1>
          <span style={{ padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
            background: "#1a0000", color: "#f85149", border: "2px solid #f85149" }}>
            {shadow?.phase7_status ?? "PHASE_7_BLOCKED"}
          </span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 6 }}>
          Live Phase 7 readiness gates · Section 7 risk rules from Phase 0 · No paper trading active
        </p>
      </div>

      {error && (
        <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 8, padding: "12px 16px", color: "#f85149", fontSize: 12, marginBottom: 16 }}>
          ⚠ Cannot reach backend: {error}
        </div>
      )}

      {/* ── Phase 7 gate status (live from shadow) ────────────────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 20 }}>
        <h3 style={{ margin: "0 0 14px", fontSize: 12, color: "#8b949e", textTransform: "uppercase" }}>
          Phase 7 Activation Gates — Live Shadow Status
        </h3>

        {loading && <div style={{ color: "#8b949e", fontSize: 12 }}>⏳ Loading shadow status…</div>}

        {!loading && shadow && (
          <>
            {/* Gate rows */}
            {Object.entries(shadow.promotion_criteria).map(([key, c]) => (
              <div key={key} style={{ display: "flex", alignItems: "center", gap: 14, padding: "10px 0", borderBottom: "1px solid #21262d" }}>
                <span style={{ fontSize: 18, fontWeight: 900, color: c.pass ? "#3fb950" : "#f85149", width: 20 }}>
                  {c.pass ? "✓" : "✗"}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: "#e6edf3", fontWeight: 600 }}>{CRIT_LABEL[key] ?? key.replace(/_/g, " ")}</div>
                  <div style={{ fontSize: 11, color: "#8b949e", marginTop: 2 }}>
                    Actual: <span style={{ color: c.pass ? "#3fb950" : "#58a6ff", fontFamily: "monospace" }}>{String(c.actual)}</span>
                    &nbsp;/&nbsp; Required: <span style={{ fontFamily: "monospace" }}>{String(c.required)}</span>
                  </div>
                </div>
                <span style={{ padding: "2px 8px", borderRadius: 6, fontSize: 10, fontWeight: 800,
                  background: c.pass ? "#1f3a1f" : "#1a0000",
                  color: c.pass ? "#3fb950" : "#f85149",
                  border: `1px solid ${c.pass ? "#2ea04366" : "#f8514966"}` }}>
                  {c.pass ? "PASS" : "PENDING"}
                </span>
              </div>
            ))}

            <div style={{ marginTop: 12, fontSize: 11, color: "#f85149", fontWeight: 700 }}>
              All gates must pass + explicit written approval before Phase 7 starts. Phase 7 is never auto-approved.
            </div>

            {/* Days progress */}
            <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid #21262d" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#8b949e", marginBottom: 6 }}>
                <span>7-day progress (day {shadow.calendar_days_observed} of 7)</span>
                <span>{shadow.days_until_review > 0 ? `${shadow.days_until_review} days remaining` : "✓ Complete"}</span>
              </div>
              <div style={{ height: 8, background: "#21262d", borderRadius: 4, overflow: "hidden" }}>
                <div style={{ width: `${Math.min((shadow.calendar_days_observed / 7) * 100, 100)}%`, height: "100%", background: "#58a6ff", borderRadius: 4 }} />
              </div>
            </div>
          </>
        )}
      </div>

      {/* ── Section 7 Risk Rules (Phase 0 plan) ──────────────────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 20 }}>
        <h3 style={{ margin: "0 0 14px", fontSize: 12, color: "#8b949e", textTransform: "uppercase" }}>
          Phase 0 Risk Rules (Will Apply in Phase 7)
        </h3>
        <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 12 }}>
          These rules are defined in the Phase 0 plan and will be enforced programmatically when Phase 7 activates.
          Currently inactive — no paper trades are running.
        </div>
        {PHASE0_RISK_RULES.map(r => (
          <div key={r.rule} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #21262d", fontSize: 12 }}>
            <span style={{ color: "#8b949e", display: "flex", gap: 8 }}><span>{r.icon}</span>{r.rule}</span>
            <span style={{ fontWeight: 600, color: r.value === "DISABLED" || r.value === "Phase 7 BLOCKED" ? "#f85149" : "#e6edf3" }}>
              {r.value}
            </span>
          </div>
        ))}
      </div>

      {/* ── Risk state legend (for when Phase 7 activates) ───────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid #30363d", fontSize: 11, color: "#8b949e", textTransform: "uppercase", fontWeight: 700 }}>
          Risk State Labels (Phase 7 Reference)
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            {[
              { state: "GREEN",  condition: "Daily loss &lt;$4 · Drawdown &lt;8% · Exposure &lt;$25", trading: "Full", color: "#3fb950" },
              { state: "YELLOW", condition: "Daily loss $4–$7 · or Drawdown 8–12%",            trading: "Reduced (no >$2 positions)", color: "#d29922" },
              { state: "RED",    condition: "Daily loss approaching $7 · Drawdown 12–14%",      trading: "Exit only — no new entries", color: "#f0883e" },
              { state: "HALTED", condition: "Daily loss ≥$7 OR Drawdown ≥15%",                  trading: "None — manual review", color: "#f85149" },
            ].map(r => (
              <tr key={r.state} style={{ borderBottom: "1px solid #21262d" }}>
                <td style={{ padding: "10px 16px", width: 80 }}>
                  <span style={{ fontWeight: 800, color: r.color, fontSize: 12 }}>{r.state}</span>
                </td>
                <td style={{ padding: "10px 16px", fontSize: 11, color: "#8b949e" }} dangerouslySetInnerHTML={{ __html: r.condition }} />
                <td style={{ padding: "10px 16px", fontSize: 11, color: "#e6edf3" }}>{r.trading}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: "10px 16px", fontSize: 11, color: "#8b949e" }}>
          Currently: <strong style={{ color: "#f85149" }}>HALTED</strong> — Paper trading not active (Phase 7 BLOCKED)
        </div>
      </div>
    </div>
  );
}
