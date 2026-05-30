import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg:      "#0d1117",
        surface: "#161b22",
        border:  "#30363d",
        text:    "#e6edf3",
        muted:   "#8b949e",
        green:   "#3fb950",
        blue:    "#58a6ff",
        purple:  "#bc8cff",
        orange:  "#f0883e",
        red:     "#f85149",
        yellow:  "#d29922",
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
