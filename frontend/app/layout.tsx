import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Weather1 — Polymarket Weather Edge Engine",
  description: "Phase 1 dashboard skeleton. Paper trading only. No real orders.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: "#0d1117" }}>
        {/* ── Phase 1 Demo Mode Banner ─────────────────────────────────────── */}
        <div
          role="alert"
          style={{
            background: "#3d1f00",
            borderBottom: "2px solid #f0883e",
            padding: "9px 24px",
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 12,
            color: "#f0883e",
            fontWeight: 600,
            flexShrink: 0,
            zIndex: 100,
          }}
        >
          <span style={{ fontSize: 15 }}>⚠️</span>
          <span>
            <strong>Phase 6F — Shadow monitoring active · PHASE_7_BLOCKED · No positions · No P&amp;L.</strong> Polymarket markets, wallet snapshot,
            weather data, and signal engine are live and read-only.
            P&amp;L and portfolio are still <strong>mock</strong>.
            No real orders. No paper trading. No private keys.
            Settlement source not verified — signals are for analysis only.
          </span>
        </div>

        {/* ── App shell ────────────────────────────────────────────────────── */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          <Sidebar />
          <main style={{ flex: 1, padding: "32px 40px", overflowY: "auto" }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
