const LOGS = [
  { id: 1, time: "2026-05-30 08:00:00", type: "data_fetch",        market: "—",       detail: "Gamma API poll — 5 weather markets cached",                         result: "ok",      module: "ingestion" },
  { id: 2, time: "2026-05-30 08:01:00", type: "signal_evaluated",  market: "mock-001", detail: "M1 score: 0.81 · M2 gap: +14.2pp · rec: ENTER",                   result: "ok",      module: "signal_engine" },
  { id: 3, time: "2026-05-30 08:01:10", type: "risk_check",        market: "mock-001", detail: "Exposure $5/$35 · Daily loss $0/$7 · Liquidity OK",                result: "ok",      module: "risk_engine" },
  { id: 4, time: "2026-05-30 08:01:11", type: "paper_trade",       market: "mock-001", detail: "Simulated BUY YES @ 0.58 + 1% slippage · Size: $2.00",             result: "ok",      module: "paper_sim" },
  { id: 5, time: "2026-05-30 08:15:00", type: "signal_evaluated",  market: "mock-005", detail: "M5 liquidity filter: $780 < $500 threshold — SKIPPED",             result: "skipped", module: "signal_engine" },
];

const resultColor: Record<string, string> = {
  ok:      "#3fb950",
  skipped: "#d29922",
  blocked: "#f0883e",
  error:   "#f85149",
};

const typeColor: Record<string, string> = {
  data_fetch:       "#8b949e",
  signal_evaluated: "#bc8cff",
  risk_check:       "#58a6ff",
  paper_trade:      "#3fb950",
};

export default function LogsPage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>📝 Execution Logs</h1>
          <span style={{ padding: "3px 10px", borderRadius: 10, fontSize: 11, fontWeight: 800,
            background: "#3d2b00", color: "#f0883e", border: "2px solid #f0883e" }}>
            ⚠ MOCK / PLACEHOLDER — not live
          </span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>
          Execution log is a placeholder. Live logging will be added when Phase 7 paper trading activates.
          These example entries are NOT real system events.
        </p>
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
        {[
          { label: "Events Today", value: "5", color: "#8b949e" },
          { label: "OK", value: "4", color: "#3fb950" },
          { label: "Skipped", value: "1", color: "#d29922" },
          { label: "Blocked", value: "0", color: "#f0883e" },
          { label: "Errors", value: "0", color: "#f85149" },
        ].map(s => (
          <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "10px 14px" }}>
            <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
              {["ID", "Timestamp", "Event Type", "Market", "Detail", "Result", "Module"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "10px 12px", fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {LOGS.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid #21262d" }}>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#8b949e", fontFamily: "monospace" }}>{l.id}</td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#8b949e", fontFamily: "monospace", whiteSpace: "nowrap" }}>{l.time}</td>
                <td style={{ padding: "10px 12px" }}>
                  <span style={{ fontSize: 10, fontWeight: 600, color: typeColor[l.type] ?? "#8b949e",
                    background: (typeColor[l.type] ?? "#8b949e") + "22", padding: "2px 7px", borderRadius: 8 }}>
                    {l.type}
                  </span>
                </td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#8b949e", fontFamily: "monospace" }}>{l.market}</td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#e6edf3", maxWidth: 300 }}>{l.detail}</td>
                <td style={{ padding: "10px 12px" }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: resultColor[l.result] ?? "#8b949e" }}>
                    {l.result.toUpperCase()}
                  </span>
                </td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: "#8b949e", fontFamily: "monospace" }}>{l.module}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
