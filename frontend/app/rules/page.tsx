const MODULES = [
  { num: 1, name: "Global/Station Temperature Edge", status: "Phase 5", purpose: "Primary signal from NOAA/NWS data vs market price", params: "Min anomaly: +0.10°C above record | Data elapsed: ≥15 days | Source agreement: ≥2" },
  { num: 2, name: "Forecast vs Market Probability Gap", status: "Phase 5", purpose: "Enter when model probability vs market implied probability gap ≥10pp", params: "Min gap: 10pp | Source agreement: ≥2 | Applies to: all weather markets" },
  { num: 3, name: "Late-Stage Profit Capture", status: "Phase 5", purpose: "Re-evaluate at 48h before resolution. Take profit at tier thresholds.", params: "+10%→close 50% | +20%→close 25% more | +40%→close all | −15%→stop-loss" },
  { num: 4, name: "Top-Wallet Confirmation", status: "Phase 3", purpose: "Secondary confirmation only. Wallets with >8% all-time efficiency.", params: "Watchlist: gopfan2, bama124, CoffeeLover, 9985, DarbySkees | Upgrades: $2→$3 position" },
  { num: 5, name: "Liquidity / Spread Filter", status: "Phase 5", purpose: "Hard gate. Block entry if market conditions are unfavourable.", params: "Min liquidity: $500 | Max spread: 5% | Min orders: 10 | Last trade: <6h | Not within 24h of resolution" },
  { num: 6, name: "Risk Engine & Kill Switch", status: "Phase 7", purpose: "Enforce all risk rules programmatically. Cannot be overridden.", params: "Daily stop: −$7 | Kill switch: −$15 | Max exposure: $35 | Stop-loss: −15%" },
  { num: 7, name: "Paper Trading Simulator", status: "Phase 7", purpose: "Simulate fills against live prices. No real orders ever.", params: "Entry: best-ask + 1% slippage | Exit: best-bid + 0.5% slippage | Resolution slippage: +1.5%" },
];

export default function RulesPage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>📋 Strategy Rules</h1>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>Weather1 Strategy v1 · Active configuration · Read-only reference</p>
      </div>

      <div style={{ background: "#1a2744", border: "1px solid #388bfd", borderRadius: 8, padding: "12px 16px", marginBottom: 24, fontSize: 12, color: "#58a6ff" }}>
        Strategy v1 · Sharp Selector archetype · $100 paper capital · No real orders before Phase 10
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {MODULES.map((m) => (
          <div key={m.num} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
              <div style={{ width: 28, height: 28, borderRadius: 6, background: "#0d1117", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: "#58a6ff", flexShrink: 0 }}>
                {m.num}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#e6edf3" }}>{m.name}</div>
                <div style={{ fontSize: 11, color: "#8b949e" }}>Active from: {m.status}</div>
              </div>
              <span style={{ padding: "2px 10px", borderRadius: 10, fontSize: 10, fontWeight: 600, background: "#21262d", color: "#8b949e", border: "1px solid #30363d" }}>
                {m.status}
              </span>
            </div>
            <div style={{ fontSize: 12, color: "#8b949e", marginBottom: 6 }}>{m.purpose}</div>
            <div style={{ fontSize: 11, fontFamily: "monospace", color: "#bc8cff", background: "#0d1117", borderRadius: 6, padding: "8px 12px" }}>{m.params}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
