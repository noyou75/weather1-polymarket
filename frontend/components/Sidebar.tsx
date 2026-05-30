"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/",           label: "Overview",            icon: "🏠" },
  { href: "/markets",    label: "Live Markets",         icon: "🌦" },
  { href: "/signals",    label: "Signal Scanner",       icon: "📡" },
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
    <aside
      style={{
        width: 220,
        minHeight: "100vh",
        background: "#161b22",
        borderRight: "1px solid #30363d",
        display: "flex",
        flexDirection: "column",
        padding: "24px 0",
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: "0 20px 24px", borderBottom: "1px solid #30363d" }}>
        <div style={{ fontSize: 16, fontWeight: 800, color: "#e6edf3" }}>
          🌦 Weather1
        </div>
        <div style={{ fontSize: 11, color: "#8b949e", marginTop: 4 }}>
          Polymarket Weather Edge
        </div>
        <div
          style={{
            marginTop: 8,
            display: "inline-block",
            padding: "2px 8px",
            background: "#1f3a1f",
            border: "1px solid #2ea043",
            borderRadius: 10,
            fontSize: 10,
            color: "#3fb950",
            fontWeight: 600,
          }}
        >
          Phase 1 · Mock Data
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: "12px 0" }}>
        {NAV.map(({ href, label, icon }) => {
          const active = path === href;
          return (
            <Link
              key={href}
              href={href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 20px",
                textDecoration: "none",
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                color: active ? "#58a6ff" : "#8b949e",
                background: active ? "#1c2a3e" : "transparent",
                borderLeft: active ? "2px solid #58a6ff" : "2px solid transparent",
                transition: "all 0.1s",
              }}
            >
              <span style={{ fontSize: 15 }}>{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div
        style={{
          padding: "16px 20px",
          borderTop: "1px solid #30363d",
          fontSize: 11,
          color: "#8b949e",
        }}
      >
        <div>$100 paper capital</div>
        <div style={{ color: "#3fb950", fontWeight: 700, marginTop: 2 }}>
          No real orders
        </div>
      </div>
    </aside>
  );
}
