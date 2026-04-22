"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { Card, Badge, SectionHeading, ProgressBar } from "@/components/ui";
import { chartTheme } from "@/lib/chart-theme";
import { tosScores, velocityAlerts, regulatorySignals, feedHealth } from "@/data/mock-data";

const impactVariant: Record<string, "red" | "amber" | "blue"> = {
  high: "red",
  medium: "amber",
  low: "blue",
};

const feedStatusColor: Record<string, "emerald" | "amber" | "red"> = {
  healthy: "emerald",
  degraded: "amber",
  down: "red",
};

export function SignalsView() {
  return (
    <div className="space-y-6">
      <SectionHeading>Demand Intelligence</SectionHeading>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* TOS Scores Chart */}
        <Card padding="md">
          <SectionHeading size="sm" as="h3">Top 10 TOS Scores</SectionHeading>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart
              data={tosScores}
              layout="vertical"
              margin={{ left: 10, right: 20, top: 0, bottom: 0 }}
            >
              <CartesianGrid {...chartTheme.grid} horizontal={false} />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fill: chartTheme.axis.stroke, fontSize: chartTheme.axis.fontSize }}
              />
              <YAxis
                dataKey="topic"
                type="category"
                width={200}
                tick={{ fill: chartTheme.axis.stroke, fontSize: 11 }}
              />
              <Tooltip
                contentStyle={chartTheme.tooltip.contentStyle}
                labelStyle={chartTheme.tooltip.labelStyle}
                formatter={(value) => [`${value}/100`, "TOS Score"]}
              />
              <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                {tosScores.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.score >= 85 ? chartTheme.colors.success : entry.score >= 70 ? chartTheme.colors.secondary : chartTheme.colors.muted}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Velocity Alerts */}
        <div className="space-y-6">
          <Card padding="md">
            <SectionHeading size="sm" as="h3">Velocity Alerts</SectionHeading>
            <div className="space-y-3">
              {velocityAlerts.map((a, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                  <div className="flex-1">
                    <div className="text-sm text-slate-200">{a.signal}</div>
                    <div className="text-xs text-slate-500">{a.source} / {a.period}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400 font-mono text-sm font-bold">+{a.change}%</span>
                    <Badge variant="emerald">trending</Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Feed Health */}
          <Card padding="md">
            <SectionHeading size="sm" as="h3">Feed Health</SectionHeading>
            <div className="space-y-3">
              {feedHealth.map((f, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                  <div className="flex-1">
                    <div className="text-sm text-slate-200">{f.name}</div>
                    <div className="text-xs text-slate-500">
                      {f.recordsProcessed} records | {(f.errorRate * 100).toFixed(1)}% error rate
                    </div>
                  </div>
                  <Badge variant={feedStatusColor[f.status]}>{f.status}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Regulatory Signals */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">Regulatory Signals (State Mandates)</SectionHeading>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">State</th>
                <th className="pb-2 pr-4">Bill</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Impact</th>
                <th className="pb-2">Effective Date</th>
              </tr>
            </thead>
            <tbody>
              {regulatorySignals.map((r, i) => (
                <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2 pr-4 text-slate-200 font-medium">{r.state}</td>
                  <td className="py-2 pr-4 text-slate-300 font-mono text-xs">{r.bill}</td>
                  <td className="py-2 pr-4">
                    <Badge variant="cyan">{r.status}</Badge>
                  </td>
                  <td className="py-2 pr-4">
                    <Badge variant={impactVariant[r.impact]}>{r.impact}</Badge>
                  </td>
                  <td className="py-2 text-slate-400">{r.effectiveDate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
