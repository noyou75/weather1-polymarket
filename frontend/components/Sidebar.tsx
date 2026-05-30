"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/",           label: "Overview",            icon: "🏠" },
  { href: "/markets",    label: "Live Markets",         icon: "🌦" },
  { href: "/signals",    label: "Signal Scanner",       icon: "📡" },
  { href: "/shadow",     label: "Shadow Monitor",       icon: "👁", live: true },
  { href: "/portfolio",  label: "Paper Portfolio",      icon: "📊" },
  { href: "/risk",       label: "Risk Monitor",         icon: "🛡" },
  { href: "/wallets",    label: "Top Wallets",          icon: "👛" },
  { href: "/backtest",   label: "Backtest Reports",     icon: "🔬" },
  { href: "/rules",      label: "Strategy Rules",       icon: "📋" },
  { href: "/logs",       label: "Execution Logs",       icon: "📝" },
];

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside style={{
      width: 220, minHeight: "100vh", background: "#161b22",
      borderRight: "1px solid #30363d", display: "flex",
      flexDirection: "column", padding: "24px 0", flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: "0 20px 24px", borderBottom: "1px solid #30363d" }}>
        <div style={{ fontSize: 16, fontWeight: 800, color: "#e6edf3" }}>🌦 Weather1</div>
        <div style={{ fontSize: 11, color: "#8b949e", marginTop: 4 }}>Polymarket Weather Edge</div>
        <div style={{
          marginTop: 8, display: "inline-block", padding: "2px 8px",
          background: "#0d2818", border: "1px solid #2ea043",
          borderRadius: 10, fontSize: 10, color: "#3fb950", fontWeight: 700,
        }}>
          Phase 6J · Live
        </div>
        <div style={{
          marginTop: 4, display: "inline-block", padding: "2px 8px",
          background: "#1a0000", border: "1px solid #f8514955",
          borderRadius: 10, fontSize: 10, color: "#f85149", fontWeight: 700,
        }}>
          Phase 7 BLOCKED
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: "12px 0" }}>
        {NAV.map(({ href, label, icon, live }) => {
          const active = path === href;
          return (
            <Link key={href} href={href} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "8px 20px", textDecoration: "none", fontSize: 13,
              fontWeight: active ? 600 : 400,
              color: active ? "#58a6ff" : "#8b949e",
              background: active ? "#1c2a3e" : "transparent",
              borderLeft: active ? "2px solid #58a6ff" : "2px solid transparent",
              transition: "all 0.1s",
            }}>
              <span style={{ fontSize: 15 }}>{icon}</span>
              <span style={{ flex: 1 }}>{label}</span>
              {live && (
                <span style={{
                  fontSize: 9, padding: "1px 5px", borderRadius: 6,
                  background: "#1f3a1f", color: "#3fb950", border: "1px solid #2ea043", fontWeight: 700,
                }}>LIVE</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: "16px 20px", borderTop: "1px solid #30363d", fontSize: 11, color: "#8b949e" }}>
        <div style={{ color: "#f85149", fontWeight: 700 }}>🚫 Phase 7 Blocked</div>
        <div style={{ marginTop: 2 }}>Shadow monitoring in progress</div>
        <div style={{ color: "#3fb950", fontWeight: 700, marginTop: 4 }}>No real orders</div>
      </div>
    </aside>
  );
}
