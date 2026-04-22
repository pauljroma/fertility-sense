"use client";

import { Card } from "./card";

interface KPICardProps {
  value: string;
  label: string;
  trend?: number;
  target?: string;
}

export function KPICard({ value, label, trend, target }: KPICardProps) {
  return (
    <Card className="text-center">
      <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
        {value}
      </div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
      {trend !== undefined && (
        <div className={`text-xs mt-1 ${trend > 0 ? "text-emerald-400" : "text-red-400"}`}>
          {trend > 0 ? "\u2191" : "\u2193"} {Math.abs(trend)}%
        </div>
      )}
      {target && (
        <div className="text-[10px] text-slate-500 mt-0.5">Target: {target}</div>
      )}
    </Card>
  );
}
