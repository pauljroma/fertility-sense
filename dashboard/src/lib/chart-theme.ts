/** Centralized Recharts theme tokens — WIN Fertility brand palette */
export const chartTheme = {
  grid: { stroke: "#334155", strokeDasharray: "3 3" },
  axis: { stroke: "#94a3b8", fontSize: 12 },
  tooltip: {
    contentStyle: {
      backgroundColor: "#1e293b",
      border: "1px solid #475569",
      borderRadius: "8px",
    },
    labelStyle: { color: "#e2e8f0" },
  },
  colors: {
    primary: "#1a4d8c",
    secondary: "#f5a623",
    success: "#10b981",
    danger: "#ef4444",
    warning: "#f59e0b",
    info: "#06b6d4",
    muted: "#94a3b8",
  },
  palette: [
    "#1a4d8c",
    "#f5a623",
    "#10b981",
    "#8b5cf6",
    "#ef4444",
    "#06b6d4",
    "#f97316",
  ],
  gradients: {
    navy: {
      id: "colorNavy",
      stops: [
        { offset: "5%", stopColor: "#1a4d8c", stopOpacity: 0.8 },
        { offset: "95%", stopColor: "#1a4d8c", stopOpacity: 0 },
      ],
    },
    gold: {
      id: "colorGold",
      stops: [
        { offset: "5%", stopColor: "#f5a623", stopOpacity: 0.8 },
        { offset: "95%", stopColor: "#f5a623", stopOpacity: 0 },
      ],
    },
  },
} as const;
