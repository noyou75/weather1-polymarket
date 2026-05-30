"use client";
import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

interface ShadowReadiness {
  phase7_status: string;
  calendar_days_observed: number;
  total_observations: number;
  days_until_review: number;
  obs_until_review: number;
  promotion_criteria: Record<string, { pass: boolean; actual: string | number; required: string | number }>;
}

export default function PortfolioPage() {
  const [readiness, setReadiness] = useState<ShadowReadiness | null>(null);

  useEffect(() => {
    fetch(apiUrl("/shadow/readiness"), { cache: "no-store" })
      .then(r => r.json())
      .then(d => setReadiness(d as ShadowReadiness))
      .catch(() => null);
  }, []);

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>📊 Paper Portfolio</h1>
          <span style={{ padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
            background: "#1a0000", color: "#f85149", border: "2px solid #f85149" }}>
            Phase 7 BLOCKED
          </span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 6 }}>
          Paper trading is not active. This page will show live paper positions once Phase 7 is approved.
        </p>
      </div>

      {/* ── BLOCKED state ──────────────────────────────────────────────────── */}
      <div style={{ background: "#1a0000", border: "2px solid #f85149", borderRadius: 12, padding: "28px 32px", marginBottom: 24, textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🚫</div>
        <div style={{ fontSize: 20, fontWeight: 900, color: "#f85149", marginBottom: 8 }}>
          Paper Trading Not Active
        </div>
        <div style={{ fontSize: 14, color: "#e6edf3", marginBottom: 8 }}>
          Phase 7 is blocked until shadow monitoring passes and you give explicit written approval.
        </div>
        <div style={{ fontSize: 12, color: "#8b949e" }}>
          No portfolio exists. No P&L exists. No positions have been created. No capital has been deployed.
        </div>
      </div>

      {/* ── Live shadow readiness ─────────────────────────────────────────── */}
      {readiness && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 24 }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 12, color: "#8b949e", textTransform: "uppercase" }}>
            Current Shadow Monitoring Progress (live)
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px,1fr))", gap: 12, marginBottom: 14 }}>
            {[
              { label: "Observations", value: `${readiness.total_observations}/30`, pass: readiness.total_observations >= 30 },
              { label: "Calendar Days", value: `${readiness.calendar_days_observed}/7`, pass: readiness.calendar_days_observed >= 7 },
              { label: "Days Remaining", value: String(readiness.days_until_review), pass: false },
              { label: "Explicit Approval", value: "Pending", pass: false },
            ].map(s => (
              <div key={s.label} style={{ background: "#0d1117", border: `1px solid ${s.pass ? "#2ea04366" : "#30363d"}`, borderRadius: 8, padding: "10px 14px" }}>
                <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: s.pass ? "#3fb950" : "#58a6ff", marginTop: 2 }}>
                  {s.pass ? "✓ " : ""}{s.value}
                </div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 11, color: "#8b949e" }}>
            → When all criteria pass and you give written approval, Phase 7 paper trading will begin.
            At that point, this page will show live paper positions, P&L, and risk metrics.
          </div>
        </div>
      )}

      {/* ── Phase 7 checklist ─────────────────────────────────────────────── */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 24 }}>
        <h3 style={{ margin: "0 0 14px", fontSize: 12, color: "#8b949e", textTransform: "uppercase" }}>
          Phase 7 Activation Requirements
        </h3>
        {[
          "✓ Strategy v1.1 passes MEDIUM-quality backtest (71.4% win rate — already done)",
          "✓ Settlement source verified: NASA GISTEMP (already done)",
          "⏳ ≥ 30 shadow observations collected",
          "⏳ ≥ 7 calendar days of live observation",
          "⏳ Average spread ≤ 5% at signal time",
          "⏳ Directional movement ≥ 0% on average",
          "🔒 Explicit written approval from you (never auto-approved)",
        ].map((item, i) => (
          <div key={i} style={{ padding: "7px 0", borderBottom: "1px solid #21262d", fontSize: 12, color: "#8b949e", display: "flex", gap: 8 }}>
            <span>{item}</span>
          </div>
        ))}
      </div>

      {/* ── MOCK placeholder — clearly labelled ──────────────────────────── */}
      <div style={{ background: "#1a1200", border: "2px dashed #f0883e55", borderRadius: 10, padding: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <h3 style={{ margin: 0, fontSize: 12, color: "#f0883e", textTransform: "uppercase" }}>
            Illustrative Layout (Paper Portfolio will look like this)
          </h3>
          <span style={{ padding: "2px 8px", borderRadius: 6, fontSize: 10, fontWeight: 800, background: "#3d2b00", color: "#f0883e", border: "1px solid #f0883e44" }}>
            MOCK EXAMPLE — NOT REAL DATA
          </span>
        </div>
        <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 12 }}>
          When Phase 7 is active, this section will show real paper trades, P&L, and positions.
          The data below is illustrative only — $0 real capital has been deployed.
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px,1fr))", gap: 10, opacity: 0.4 }}>
          {[
            { label: "Paper Capital", value: "$100.00" },
            { label: "Deployed",      value: "$0.00"   },
            { label: "Realised P&L",  value: "$0.00"   },
            { label: "Win Rate",       value: "—"       },
            { label: "Open Positions", value: "0"       },
          ].map(s => (
            <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "10px 14px" }}>
              <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#8b949e" }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
