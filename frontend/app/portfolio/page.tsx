import MockChart from "@/components/MockChart";

const EQUITY = [
  { date: "May 10", capital: 100.00 },
  { date: "May 15", capital: 100.67 },
  { date: "May 20", capital: 101.10 },
  { date: "May 25", capital: 101.77 },
  { date: "May 30", capital: 102.04 },
];

const OPEN = [
  { market: "Will July 2026 be the hottest July on record?", side: "YES", entry: 0.58, current: 0.62, size: "$2.00", stop: "0.493", pnl: "+$0.14", pnlPct: "+6.9%", modules: "M1+M2" },
  { market: "Will 2026 be the hottest year on record globally?", side: "YES", entry: 0.68, current: 0.71, size: "$3.00", stop: "0.578", pnl: "+$0.13", pnlPct: "+4.4%", modules: "M1+M2+M4" },
];

const CLOSED = [
  { market: "Was May 2026 anomaly above +1.3°C?", side: "YES", entry: 0.54, exit: 0.72, size: "$2.00", pnl: "+$0.67", pnlPct: "+33.3%", date: "May 25" },
];

export default function PortfolioPage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>📊 Paper Portfolio</h1>
          <span style={{
            padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
            background: "#3d2b00", color: "#f0883e", border: "2px solid #f0883e",
            letterSpacing: "0.5px", textTransform: "uppercase",
          }}>
            ⚠ Mock P&amp;L
          </span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>Hardcoded demo data · No paper trading active · Phase 7: replaced with live paper trading simulator</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 14, marginBottom: 24 }}>
        {[
          { label: "Starting Capital", value: "$100.00", color: "#8b949e" },
          { label: "Current Capital", value: "$102.04", color: "#3fb950" },
          { label: "Deployed", value: "$5.00", color: "#58a6ff" },
          { label: "Realised P&L", value: "+$1.77", color: "#3fb950" },
          { label: "Unrealised P&L", value: "+$0.27", color: "#3fb950" },
          { label: "Win Rate", value: "100%", color: "#3fb950" },
        ].map(s => (
          <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "12px 16px" }}>
            <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: 20, marginBottom: 24 }}>
        <MockChart data={EQUITY} height={140} color="#3fb950" label="Paper Portfolio Equity ($)" />
      </div>

      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden", marginBottom: 20 }}>
        <div style={{ padding: "14px 16px", borderBottom: "1px solid #30363d", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>Open Positions ({OPEN.length})</div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
              {["Market", "Side", "Entry", "Current", "Size", "Stop", "Unrealised P&L", "Modules"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {OPEN.map((p, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #21262d" }}>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#e6edf3", maxWidth: 280 }}>{p.market}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>{p.side}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, color: "#8b949e", fontFamily: "monospace" }}>{p.entry}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, fontFamily: "monospace" }}>{p.current}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, color: "#58a6ff" }}>{p.size}</td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#f85149", fontFamily: "monospace" }}>{p.stop}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>{p.pnl} ({p.pnlPct})</td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#bc8cff" }}>{p.modules}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
        <div style={{ padding: "14px 16px", borderBottom: "1px solid #30363d", fontSize: 12, fontWeight: 700, color: "#8b949e" }}>Closed Trades ({CLOSED.length})</div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
              {["Market", "Side", "Entry", "Exit", "Size", "P&L", "Closed"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CLOSED.map((p, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #21262d" }}>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#e6edf3", maxWidth: 280 }}>{p.market}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>{p.side}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, color: "#8b949e", fontFamily: "monospace" }}>{p.entry}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, fontFamily: "monospace" }}>{p.exit}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, color: "#58a6ff" }}>{p.size}</td>
                <td style={{ padding: "10px 12px", fontSize: 12, fontWeight: 700, color: "#3fb950" }}>{p.pnl} ({p.pnlPct})</td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#8b949e" }}>{p.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
