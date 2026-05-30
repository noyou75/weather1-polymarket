"use client";
import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

interface LiveMarket {
  market_id: string;
  question: string;
  event_title: string | null;
  end_date: string | null;
  yes_price: number | null;
  no_price: number | null;
  best_bid: number | null;
  best_ask: number | null;
  spread: number | null;
  liquidity: number | null;
  volume: number | null;
  volume_24hr: number | null;
  is_active: boolean;
  accepting_orders: boolean;
  signal_flag: string | null;
  data_source: string;
  fetched_at: string | null;
}

interface ApiResponse {
  count: number;
  data_source: string;
  warning?: string;
  markets: LiveMarket[];
}

function fmt(n: number | null | undefined, prefix = "$"): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${prefix}${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${prefix}${(n / 1_000).toFixed(1)}K`;
  return `${prefix}${n.toFixed(0)}`;
}

function daysTo(iso: string | null): string {
  if (!iso) return "—";
  const diff = new Date(iso).getTime() - Date.now();
  const days = Math.ceil(diff / 86_400_000);
  return days <= 0 ? "resolved" : `${days}d`;
}

function spreadColor(s: number | null): string {
  if (s == null) return "#8b949e";
  if (s <= 0.02) return "#3fb950";
  if (s <= 0.05) return "#d29922";
  return "#f85149";
}

function LiquidityBadge({ liq }: { liq: number | null }) {
  if (liq == null) return <span style={{ color: "#8b949e" }}>—</span>;
  const color = liq >= 10_000 ? "#3fb950" : liq >= 1_000 ? "#d29922" : "#f85149";
  return <span style={{ color, fontWeight: 600 }}>{fmt(liq)}</span>;
}

export default function MarketsPage() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minLiq, setMinLiq] = useState(0);
  const [search, setSearch] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiUrl("/markets/weather")}?min_liquidity=${minLiq}`, {
        cache: "no-store",
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json: ApiResponse = await resp.json();
      setData(json);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [minLiq]);  // eslint-disable-line react-hooks/exhaustive-deps

  const isMock = data?.data_source === "mock_fallback";
  const isLive = data?.data_source === "gamma_api";

  const markets = (data?.markets ?? []).filter(m => {
    if (!search) return true;
    return m.question.toLowerCase().includes(search.toLowerCase()) ||
           (m.event_title ?? "").toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>🌦 Live Weather Markets</h1>
          {isLive && (
            <span style={{
              padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
              background: "#1f3a1f", color: "#3fb950", border: "1px solid #2ea043",
            }}>✓ Live · Read-Only · Gamma API</span>
          )}
          {isMock && (
            <span style={{
              padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
              background: "#3d2b00", color: "#f0883e", border: "2px solid #f0883e",
            }}>⚠ Mock Fallback</span>
          )}
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 4 }}>
          {isLive
            ? "Live read-only data from Polymarket Gamma API · No orders · No paper trading yet"
            : isMock
            ? "Backend not connected or no markets fetched yet — showing placeholder data"
            : "Connecting..."}
        </p>
      </div>

      {/* Safety banner */}
      <div style={{
        background: "#0d2818", border: "1px solid #2ea043", borderRadius: 8,
        padding: "10px 16px", marginBottom: 18, fontSize: 12, color: "#3fb950",
      }}>
        🔒 Read-only data mode — No real orders placed. No paper trading active. No Polymarket write calls.
      </div>

      {/* Warning if mock */}
      {isMock && data?.warning && (
        <div style={{
          background: "#3d2b00", border: "1px solid #f0883e", borderRadius: 8,
          padding: "10px 16px", marginBottom: 16, fontSize: 12, color: "#f0883e",
        }}>
          ⚠ {data.warning}
        </div>
      )}

      {/* Stat chips */}
      {data && (
        <div style={{ display: "flex", gap: 14, marginBottom: 18, flexWrap: "wrap" }}>
          {[
            { label: "Total Markets", value: String(data.count), color: "#58a6ff" },
            { label: "Shown", value: String(markets.length), color: "#e6edf3" },
            { label: "Data Source", value: isLive ? "Gamma API" : "Mock", color: isLive ? "#3fb950" : "#f0883e" },
          ].map(s => (
            <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "10px 14px" }}>
              <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase" }}>{s.label}</div>
              <div style={{ fontSize: 17, fontWeight: 800, color: s.color }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search question or event…"
          style={{
            background: "#161b22", border: "1px solid #30363d", color: "#e6edf3",
            padding: "6px 12px", borderRadius: 6, fontSize: 13, width: 260,
          }}
        />
        <select
          value={minLiq}
          onChange={e => setMinLiq(Number(e.target.value))}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3", padding: "6px 12px", borderRadius: 6, fontSize: 13 }}
        >
          <option value={0}>All liquidity</option>
          <option value={500}>≥ $500</option>
          <option value={1000}>≥ $1K</option>
          <option value={5000}>≥ $5K</option>
          <option value={10000}>≥ $10K</option>
        </select>
        <button
          onClick={load}
          style={{ background: "#1c2a3e", border: "1px solid #388bfd", color: "#58a6ff", padding: "6px 14px", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
        >
          ↻ Refresh
        </button>
      </div>

      {/* States */}
      {loading && (
        <div style={{ padding: 40, textAlign: "center", color: "#8b949e", fontSize: 14 }}>
          ⏳ Fetching from Gamma API…
        </div>
      )}

      {error && !loading && (
        <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 8, padding: "16px 20px", color: "#f85149", fontSize: 13 }}>
          <strong>Backend connection error:</strong> {error}
          <div style={{ marginTop: 8, color: "#8b949e", fontSize: 11 }}>
            Make sure the backend is running: <code>cd backend && uv run uvicorn main:app --reload --port 8000</code>
          </div>
        </div>
      )}

      {!loading && !error && markets.length === 0 && (
        <div style={{ padding: 40, textAlign: "center", color: "#8b949e" }}>
          No markets match the current filter. Try reducing the minimum liquidity or clearing the search.
        </div>
      )}

      {/* Market table */}
      {!loading && !error && markets.length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
                {["Event / Market", "Bid", "Ask", "Spread", "Liquidity", "Vol 24h", "Ends", "Orders"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "10px 12px", fontSize: 10, color: "#8b949e", textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {markets.slice(0, 200).map((m) => (
                <tr key={m.market_id} style={{ borderBottom: "1px solid #21262d" }}>
                  <td style={{ padding: "10px 12px", maxWidth: 380 }}>
                    <div style={{ fontSize: 12, color: "#e6edf3", lineHeight: 1.4 }}>{m.question}</div>
                    {m.event_title && m.event_title !== m.question && (
                      <div style={{ fontSize: 10, color: "#8b949e", marginTop: 2 }}>📁 {m.event_title}</div>
                    )}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 13, fontWeight: 700, color: "#3fb950", fontFamily: "monospace", whiteSpace: "nowrap" }}>
                    {m.best_bid?.toFixed(3) ?? "—"}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 13, color: "#f85149", fontFamily: "monospace", whiteSpace: "nowrap" }}>
                    {m.best_ask?.toFixed(3) ?? "—"}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 12, fontFamily: "monospace", color: spreadColor(m.spread), whiteSpace: "nowrap" }}>
                    {m.spread != null ? (m.spread * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td style={{ padding: "10px 12px", whiteSpace: "nowrap" }}>
                    <LiquidityBadge liq={m.liquidity} />
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 12, color: "#58a6ff", whiteSpace: "nowrap" }}>
                    {fmt(m.volume_24hr)}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 11, color: "#8b949e", whiteSpace: "nowrap" }}>
                    {daysTo(m.end_date)}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 11, whiteSpace: "nowrap" }}>
                    {m.accepting_orders
                      ? <span style={{ color: "#3fb950" }}>✓</span>
                      : <span style={{ color: "#30363d" }}>—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {markets.length > 200 && (
            <div style={{ padding: "10px 16px", color: "#8b949e", fontSize: 11 }}>
              Showing 200 of {markets.length} markets. Use the liquidity filter to narrow results.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
