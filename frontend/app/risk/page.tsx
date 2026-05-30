function GaugeBar({ value, max, color, label }: { value: number; max: number; color: string; label: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 12 }}>
        <span style={{ color: "#8b949e" }}>{label}</span>
        <span style={{ color, fontWeight: 700 }}>{value.toFixed(2)} / {max}</span>
      </div>
      <div style={{ height: 10, background: "#30363d", borderRadius: 5, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 5, transition: "width 0.3s" }} />
      </div>
    </div>
  );
}

export default function RiskPage() {
  const state = "GREEN";
  const stateColor = { GREEN: "#3fb950", YELLOW: "#d29922", RED: "#f85149", HALTED: "#f85149" }[state] ?? "#8b949e";

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>🛡 Risk Monitor</h1>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>Mock data · Phase 7: live risk engine enforcement</p>
      </div>

      {/* State badge */}
      <div style={{ background: "#161b22", border: `1px solid ${stateColor}`, borderRadius: 10, padding: "16px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ fontSize: 32, fontWeight: 900, color: stateColor }}>{state}</div>
        <div>
          <div style={{ fontSize: 13, color: "#e6edf3" }}>All limits within safe range</div>
          <div style={{ fontSize: 11, color: "#8b949e" }}>Kill switch inactive · Daily stop inactive</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Gauges */}
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20 }}>
          <h3 style={{ fontSize: 12, color: "#8b949e", textTransform: "uppercase", margin: "0 0 16px" }}>Live Limits</h3>
          <GaugeBar value={0.00} max={15.00} color="#3fb950" label="Drawdown ($)" />
          <GaugeBar value={0.00} max={7.00}  color="#3fb950" label="Daily Loss ($)" />
          <GaugeBar value={5.00} max={35.00} color="#58a6ff" label="Open Exposure ($)" />
          <GaugeBar value={2}    max={10}    color="#bc8cff" label="Open Positions" />
        </div>

        {/* Rules summary */}
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20 }}>
          <h3 style={{ fontSize: 12, color: "#8b949e", textTransform: "uppercase", margin: "0 0 16px" }}>Active Rules</h3>
          {[
            ["Default position size", "$2.00"],
            ["Max position size", "$5.00"],
            ["Max open exposure", "$35.00"],
            ["Daily soft stop", "−$7.00 (7%)"],
            ["Portfolio kill switch", "−$15.00 (15%)"],
            ["Stop-loss per trade", "−15%"],
            ["Take-profit tier 1", "+10% → close 50%"],
            ["Take-profit tier 2", "+20% → close 25%"],
            ["Take-profit tier 3", "+40% → close all"],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid #21262d", fontSize: 12 }}>
              <span style={{ color: "#8b949e" }}>{k}</span>
              <span style={{ color: "#e6edf3", fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* State legend */}
      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid #30363d", fontSize: 12, fontWeight: 700, color: "#8b949e", textTransform: "uppercase" }}>Risk States</div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            {[
              { state: "GREEN", condition: "Daily loss <$4 · Drawdown <8% · Exposure <$25", trading: "Full", color: "#3fb950" },
              { state: "YELLOW", condition: "Daily loss $4–$7 · or Drawdown 8–12% · or Exposure $25–$35", trading: "Reduced (no >$2 positions)", color: "#d29922" },
              { state: "RED", condition: "Daily loss approaching $7 · Drawdown 12–14%", trading: "Exit only — no new entries", color: "#f0883e" },
              { state: "HALTED", condition: "Daily loss ≥$7 OR Drawdown ≥15%", trading: "None — manual review required", color: "#f85149" },
            ].map(r => (
              <tr key={r.state} style={{ borderBottom: "1px solid #21262d" }}>
                <td style={{ padding: "10px 16px", width: 80 }}>
                  <span style={{ fontWeight: 800, color: r.color, fontSize: 12 }}>{r.state}</span>
                </td>
                <td style={{ padding: "10px 16px", fontSize: 11, color: "#8b949e" }}>{r.condition}</td>
                <td style={{ padding: "10px 16px", fontSize: 11, color: "#e6edf3" }}>{r.trading}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
