"use client";
import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────
interface Wallet {
  rank: number;
  wallet_address: string;
  username: string | null;
  x_username: string | null;
  verified: boolean;
  pnl_usd: number;
  volume_usd: number;
  efficiency_pct: number;
  strategies: string[];
  on_watchlist: boolean;
  watchlist_reason: string | null;
  snapshot_date: string;
}

interface WalletsResponse {
  count: number;
  total_in_db: number;
  data_source: string;
  wallets: Wallet[];
  warning?: string;
}

interface StrategyDist {
  total_wallets: number;
  distribution: Record<string, number>;
}

interface WalletSummary {
  total_wallets: number;
  watchlist_size: number;
  top50_pnl_threshold: number;
  top50_efficiency_threshold: number | null;
  top3_by_efficiency: { rank: number; username: string; efficiency_pct: number }[];
  strategy_distribution: Record<string, number>;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const STRATEGY_COLORS: Record<string, string> = {
  "Sharp Selector": "#f0883e",
  "Swing Trader":   "#58a6ff",
  "Volume Whale":   "#bc8cff",
  "Multi-Wallet":   "#f85149",
  "Domain Expert":  "#3fb950",
  "Bot / Algo":     "#58a6ff",
};

const STRATEGY_BG: Record<string, string> = {
  "Sharp Selector": "#3d2b00",
  "Swing Trader":   "#1c2a3e",
  "Volume Whale":   "#2d1f3d",
  "Multi-Wallet":   "#3d1f1f",
  "Domain Expert":  "#1f3a1f",
  "Bot / Algo":     "#1a2744",
};

function fmt(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

function StrategyBadge({ s }: { s: string }) {
  return (
    <span style={{
      padding: "2px 7px", borderRadius: 8, fontSize: 10, fontWeight: 700,
      background: STRATEGY_BG[s] ?? "#21262d",
      color: STRATEGY_COLORS[s] ?? "#8b949e",
      border: `1px solid ${STRATEGY_COLORS[s] ?? "#30363d"}44`,
      whiteSpace: "nowrap",
    }}>{s}</span>
  );
}

function EffBar({ pct }: { pct: number }) {
  const color = pct >= 20 ? "#3fb950" : pct >= 8 ? "#f0883e" : pct >= 3 ? "#d29922" : "#8b949e";
  const w = Math.min(pct / 55 * 100, 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ width: 52, height: 6, background: "#30363d", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${w}%`, height: "100%", background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color }}>{pct.toFixed(1)}%</span>
    </div>
  );
}

// ── Page component ────────────────────────────────────────────────────────────
export default function WalletsPage() {
  const [walletsData, setWalletsData] = useState<WalletsResponse | null>(null);
  const [summary, setSummary]         = useState<WalletSummary | null>(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  // Filters
  const [search, setSearch]         = useState("");
  const [stratFilter, setStratFilter] = useState("");
  const [minEff, setMinEff]         = useState(0);
  const [maxRank, setMaxRank]       = useState(100);
  const [showWatchlistOnly, setShowWatchlistOnly] = useState(false);

  // ── Data loading ────────────────────────────────────────────────────────────
  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        min_efficiency: String(minEff),
        max_rank: String(maxRank),
        ...(stratFilter && { strategy: stratFilter }),
        ...(search && { search }),
      });
      const [wRes, sRes] = await Promise.all([
        fetch(`${apiUrl("/wallets/top")}?${params}`, { cache: "no-store" }),
        fetch(apiUrl("/wallets/summary"),              { cache: "no-store" }),
      ]);
      if (!wRes.ok) throw new Error(`Wallets API: HTTP ${wRes.status}`);
      setWalletsData(await wRes.json());
      if (sRes.ok) setSummary(await sRes.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [minEff, maxRank, stratFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  // Client-side search + watchlist filter (fast, no re-fetch)
  const wallets = (walletsData?.wallets ?? []).filter(w => {
    if (showWatchlistOnly && !w.on_watchlist) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (w.username ?? "").toLowerCase().includes(q) ||
           w.wallet_address.toLowerCase().includes(q);
  });

  const isLive = walletsData?.data_source === "local_snapshot";
  const notImported = walletsData?.data_source === "not_imported";
  const dist = summary?.strategy_distribution ?? {};

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#e6edf3", margin: 0 }}>👛 Top Wallet Tracker</h1>
          <span style={{
            padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 800,
            background: "#1a2744", color: "#58a6ff", border: "1px solid #388bfd",
          }}>📸 Static Top 100 Snapshot</span>
          <span style={{
            padding: "3px 12px", borderRadius: 12, fontSize: 11, fontWeight: 700,
            background: "#21262d", color: "#8b949e", border: "1px solid #30363d",
          }}>Not live wallet polling yet</span>
        </div>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: 6 }}>
          All-time PnL leaderboard · Polymarket Weather category · May 2026 snapshot ·
          Parsed from local HTML file
        </p>
      </div>

      {/* ── Safety note ────────────────────────────────────────────────────── */}
      <div style={{
        background: "#1a2744", border: "1px solid #388bfd", borderRadius: 8,
        padding: "10px 16px", marginBottom: 18, fontSize: 12, color: "#58a6ff",
        display: "flex", gap: 8, alignItems: "flex-start",
      }}>
        <span>ℹ️</span>
        <span>
          <strong>Confirmation signal only — not blind copy-trading.</strong>{" "}
          These wallets are used as Module 4 confirmation: a watchlist trade may
          upgrade an existing signal from "watch" to "enter." They never trigger
          an independent trade on their own. No private keys. No real orders.
        </span>
      </div>

      {/* ── Error state ────────────────────────────────────────────────────── */}
      {error && (
        <div style={{ background: "#3d1f1f", border: "1px solid #f85149", borderRadius: 8, padding: "14px 18px", color: "#f85149", fontSize: 13, marginBottom: 16 }}>
          <strong>Backend error:</strong> {error}
          <div style={{ marginTop: 6, color: "#8b949e", fontSize: 11 }}>
            Run backend: <code>cd backend && uv run uvicorn main:app --reload --port 8000</code>
            {" "} then: <code>POST /api/wallets/import-top100</code>
          </div>
        </div>
      )}

      {/* ── Not imported warning ───────────────────────────────────────────── */}
      {notImported && (
        <div style={{ background: "#3d2b00", border: "1px solid #f0883e", borderRadius: 8, padding: "14px 18px", color: "#f0883e", fontSize: 13, marginBottom: 16 }}>
          ⚠ No wallets in database yet. Call <code>POST /api/wallets/import-top100</code> to parse the local snapshot.
        </div>
      )}

      {/* ── Summary stats ──────────────────────────────────────────────────── */}
      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px,1fr))", gap: 14, marginBottom: 22 }}>
          {[
            { label: "Wallets Parsed",    value: String(summary.total_wallets),                          color: "#58a6ff" },
            { label: "On Watchlist",      value: String(summary.watchlist_size),                         color: "#3fb950" },
            { label: "Top-50 PnL Floor",  value: fmt(summary.top50_pnl_threshold),                      color: "#d29922" },
            { label: "Top-50 Efficiency", value: summary.top50_efficiency_threshold != null ? `${summary.top50_efficiency_threshold.toFixed(2)}%` : "—", color: "#bc8cff" },
            { label: "Snapshot",          value: "May 2026",                                             color: "#8b949e" },
          ].map(s => (
            <div key={s.label} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "12px 16px" }}>
              <div style={{ fontSize: 10, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px" }}>{s.label}</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: s.color, marginTop: 2 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Strategy distribution ──────────────────────────────────────────── */}
      {Object.keys(dist).length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "16px 20px", marginBottom: 22 }}>
          <div style={{ fontSize: 12, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>
            Strategy Type Distribution — Top 100
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {Object.entries(dist)
              .sort(([, a], [, b]) => b - a)
              .map(([strat, count]) => (
                <div key={strat} style={{
                  background: STRATEGY_BG[strat] ?? "#21262d",
                  border: `1px solid ${STRATEGY_COLORS[strat] ?? "#30363d"}55`,
                  borderRadius: 8, padding: "8px 14px",
                  display: "flex", flexDirection: "column", gap: 2, minWidth: 100,
                }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: STRATEGY_COLORS[strat] ?? "#8b949e" }}>{strat}</span>
                  <span style={{ fontSize: 18, fontWeight: 900, color: STRATEGY_COLORS[strat] ?? "#e6edf3" }}>{count}</span>
                  <span style={{ fontSize: 10, color: "#8b949e" }}>of 100 traders</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* ── Top efficiency spotlight ───────────────────────────────────────── */}
      {summary?.top3_by_efficiency && summary.top3_by_efficiency.length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, padding: "16px 20px", marginBottom: 22 }}>
          <div style={{ fontSize: 12, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>
            Highest Efficiency Traders (Model for Strategy v1)
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {summary.top3_by_efficiency.map(w => (
              <div key={w.rank} style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 8, padding: "10px 16px", minWidth: 140 }}>
                <div style={{ fontSize: 11, color: "#d29922", fontWeight: 800 }}>#{w.rank}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#e6edf3" }}>{w.username ?? "—"}</div>
                <div style={{ fontSize: 18, fontWeight: 900, color: "#3fb950" }}>{w.efficiency_pct.toFixed(1)}%</div>
                <div style={{ fontSize: 10, color: "#8b949e" }}>efficiency</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Filters ────────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search username or wallet…"
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3", padding: "6px 12px", borderRadius: 6, fontSize: 13, width: 230 }}
        />
        <select
          value={stratFilter}
          onChange={e => setStratFilter(e.target.value)}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3", padding: "6px 12px", borderRadius: 6, fontSize: 13 }}
        >
          <option value="">All strategies</option>
          {["Sharp Selector","Swing Trader","Volume Whale","Multi-Wallet","Domain Expert","Bot / Algo"].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={minEff}
          onChange={e => setMinEff(Number(e.target.value))}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3", padding: "6px 12px", borderRadius: 6, fontSize: 13 }}
        >
          <option value={0}>All efficiency</option>
          <option value={8}>≥ 8% (watchlist)</option>
          <option value={15}>≥ 15%</option>
          <option value={20}>≥ 20%</option>
        </select>
        <select
          value={maxRank}
          onChange={e => setMaxRank(Number(e.target.value))}
          style={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3", padding: "6px 12px", borderRadius: 6, fontSize: 13 }}
        >
          <option value={100}>All ranks (1–100)</option>
          <option value={10}>Top 10</option>
          <option value={25}>Top 25</option>
          <option value={50}>Top 50</option>
        </select>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#e6edf3", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={showWatchlistOnly}
            onChange={e => setShowWatchlistOnly(e.target.checked)}
            style={{ accentColor: "#3fb950" }}
          />
          Watchlist only
        </label>
        <button
          onClick={load}
          style={{ background: "#1c2a3e", border: "1px solid #388bfd", color: "#58a6ff", padding: "6px 14px", borderRadius: 6, fontSize: 13, cursor: "pointer" }}
        >
          ↻ Refresh
        </button>
        {walletsData && (
          <span style={{ fontSize: 12, color: "#8b949e" }}>
            Showing {wallets.length} of {walletsData.total_in_db}
          </span>
        )}
      </div>

      {/* ── Loading ─────────────────────────────────────────────────────────── */}
      {loading && (
        <div style={{ padding: 40, textAlign: "center", color: "#8b949e" }}>
          ⏳ Loading wallet data…
        </div>
      )}

      {/* ── Main wallet table ──────────────────────────────────────────────── */}
      {!loading && !error && wallets.length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 10, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #30363d", background: "#0d1117" }}>
                {["Rank","Username","All-Time PnL","Volume","Efficiency","Strategy","Watchlist"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "10px 12px", fontSize: 10, color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.4px" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {wallets.map(w => (
                <tr key={w.wallet_address} style={{ borderBottom: "1px solid #21262d" }}>

                  {/* Rank */}
                  <td style={{ padding: "10px 12px" }}>
                    <span style={{
                      fontSize: 14, fontWeight: 900,
                      color: w.rank <= 3 ? "#d29922" : w.rank <= 10 ? "#f0883e" : "#8b949e",
                    }}>#{w.rank}</span>
                  </td>

                  {/* Username + wallet */}
                  <td style={{ padding: "10px 12px" }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#e6edf3" }}>
                      {w.username ?? "(unnamed)"}
                      {w.verified && <span style={{ marginLeft: 4, fontSize: 10, color: "#58a6ff" }}>✓</span>}
                    </div>
                    <div style={{ fontSize: 10, color: "#8b949e", fontFamily: "monospace" }}>
                      {w.wallet_address.slice(0, 10)}…{w.wallet_address.slice(-6)}
                    </div>
                    {w.x_username && (
                      <div style={{ fontSize: 10, color: "#58a6ff" }}>@{w.x_username}</div>
                    )}
                  </td>

                  {/* PnL */}
                  <td style={{ padding: "10px 12px", fontSize: 13, fontWeight: 700, color: "#3fb950" }}>
                    +{fmt(w.pnl_usd)}
                  </td>

                  {/* Volume */}
                  <td style={{ padding: "10px 12px", fontSize: 12, color: "#58a6ff" }}>
                    {fmt(w.volume_usd)}
                  </td>

                  {/* Efficiency bar */}
                  <td style={{ padding: "10px 12px" }}>
                    <EffBar pct={w.efficiency_pct} />
                  </td>

                  {/* Strategy badges */}
                  <td style={{ padding: "10px 12px" }}>
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {w.strategies.map(s => <StrategyBadge key={s} s={s} />)}
                    </div>
                  </td>

                  {/* Watchlist indicator */}
                  <td style={{ padding: "10px 12px" }}>
                    {w.on_watchlist ? (
                      <div>
                        <span style={{ color: "#3fb950", fontWeight: 700, fontSize: 12 }}>✓ M4</span>
                        <div style={{ fontSize: 10, color: "#8b949e", marginTop: 2 }}>
                          {w.watchlist_reason?.split("·")[0].trim()}
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: "#30363d", fontSize: 12 }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Empty state ─────────────────────────────────────────────────────── */}
      {!loading && !error && wallets.length === 0 && !notImported && (
        <div style={{ padding: 40, textAlign: "center", color: "#8b949e", background: "#161b22", borderRadius: 10, border: "1px solid #30363d" }}>
          No wallets match the current filters.
        </div>
      )}

      {/* ── Footer note ─────────────────────────────────────────────────────── */}
      <div style={{ marginTop: 20, fontSize: 11, color: "#8b949e", lineHeight: 1.6 }}>
        <strong style={{ color: "#30363d" }}>Data notes:</strong> Static snapshot from Polymarket weather leaderboard (May 2026).
        Strategy classifications are analytical inferences — not official Polymarket designations.
        Efficiency = PnL ÷ Volume × 100. Watchlist criteria: efficiency {">"} 8% AND Sharp Selector strategy.
        Phase 3 — live wallet polling not yet active (Phase 3 roadmap item).
      </div>
    </div>
  );
}
