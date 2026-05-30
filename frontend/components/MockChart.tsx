"use client";

interface Point { date: string; capital: number }

interface MockChartProps {
  data: Point[];
  height?: number;
  color?: string;
  label?: string;
}

export default function MockChart({
  data,
  height = 140,
  color = "#3fb950",
  label = "Equity Curve",
}: MockChartProps) {
  if (!data || data.length < 2) return null;

  const values = data.map((d) => d.capital);
  const min = Math.min(...values) * 0.998;
  const max = Math.max(...values) * 1.002;
  const range = max - min || 1;

  const W = 480;
  const H = height;
  const PAD = { top: 10, right: 16, bottom: 24, left: 48 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  const toX = (i: number) => PAD.left + (i / (data.length - 1)) * innerW;
  const toY = (v: number) => PAD.top + innerH - ((v - min) / range) * innerH;

  const pathD = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${toX(i)} ${toY(d.capital)}`)
    .join(" ");

  const areaD =
    pathD +
    ` L ${toX(data.length - 1)} ${PAD.top + innerH} L ${PAD.left} ${PAD.top + innerH} Z`;

  // Y-axis ticks
  const ticks = [min, min + range * 0.5, max];

  return (
    <div style={{ background: "#0d1117", borderRadius: 8, padding: "12px 8px 4px" }}>
      <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 4, paddingLeft: 8 }}>
        {label}
      </div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
        {/* Y-axis ticks */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line
              x1={PAD.left}
              y1={toY(t)}
              x2={PAD.left + innerW}
              y2={toY(t)}
              stroke="#30363d"
              strokeDasharray="3 3"
              strokeWidth={0.5}
            />
            <text
              x={PAD.left - 4}
              y={toY(t) + 4}
              textAnchor="end"
              fontSize={9}
              fill="#8b949e"
            >
              ${t.toFixed(2)}
            </text>
          </g>
        ))}

        {/* Area fill */}
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.18} />
            <stop offset="100%" stopColor={color} stopOpacity={0.01} />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#areaGrad)" />

        {/* Line */}
        <path d={pathD} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" />

        {/* X-axis labels */}
        {data
          .filter((_, i) => i === 0 || i === data.length - 1)
          .map((d, i, arr) => (
            <text
              key={i}
              x={i === 0 ? PAD.left : PAD.left + innerW}
              y={H - 4}
              textAnchor={i === 0 ? "start" : "end"}
              fontSize={9}
              fill="#8b949e"
            >
              {d.date}
            </text>
          ))}

        {/* Current value dot */}
        <circle
          cx={toX(data.length - 1)}
          cy={toY(data[data.length - 1].capital)}
          r={3}
          fill={color}
        />
      </svg>
    </div>
  );
}
