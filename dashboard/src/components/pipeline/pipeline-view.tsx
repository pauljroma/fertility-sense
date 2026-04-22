"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { Card, KPICard, SectionHeading, Badge } from "@/components/ui";
import { chartTheme } from "@/lib/chart-theme";
import { pipelineSummary, pipelineStages, buyerTypes, staleDeals } from "@/data/mock-data";

const buyerPieData = buyerTypes.map((b) => ({ name: b.type, value: b.value }));

function fmt(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n}`;
}

export function PipelineView() {
  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard value={fmt(pipelineSummary.totalPipelineValue)} label="Total Pipeline" trend={12} />
        <KPICard value={String(pipelineSummary.dealsInPipeline)} label="Deals in Pipeline" trend={5} />
        <KPICard value={fmt(pipelineSummary.weightedValue)} label="Weighted Value" trend={8} />
        <KPICard value={String(pipelineSummary.staleDeals)} label="Stale Deals" trend={-2} />
        <KPICard value={`${pipelineSummary.winRate}%`} label="Win Rate" trend={3} target="35%" />
        <KPICard value={fmt(pipelineSummary.avgDealSize)} label="Avg Deal Size" trend={6} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Funnel */}
        <Card padding="md">
          <SectionHeading size="sm">Deal Funnel</SectionHeading>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pipelineStages} layout="vertical" margin={{ left: 20, right: 20 }}>
              <CartesianGrid {...chartTheme.grid} horizontal={false} />
              <XAxis type="number" tick={{ fill: chartTheme.axis.stroke, fontSize: chartTheme.axis.fontSize }} />
              <YAxis
                dataKey="stage"
                type="category"
                tick={{ fill: chartTheme.axis.stroke, fontSize: chartTheme.axis.fontSize }}
                width={90}
              />
              <Tooltip
                contentStyle={chartTheme.tooltip.contentStyle}
                labelStyle={chartTheme.tooltip.labelStyle}
                formatter={(value) => [fmt(value as number), "Value"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {pipelineStages.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Buyer Type Breakdown */}
        <Card padding="md">
          <SectionHeading size="sm">Pipeline by Buyer Type</SectionHeading>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={buyerPieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              >
                {buyerPieData.map((_, i) => (
                  <Cell key={i} fill={chartTheme.palette[i % chartTheme.palette.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={chartTheme.tooltip.contentStyle}
                labelStyle={chartTheme.tooltip.labelStyle}
                formatter={(value) => [fmt(value as number), "Value"]}
              />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                wrapperStyle={{ fontSize: 12, color: "#94a3b8" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Stale Deals Table */}
      <Card padding="md">
        <SectionHeading size="sm">Stale Deals Alert</SectionHeading>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">Company</th>
                <th className="pb-2 pr-4">Stage</th>
                <th className="pb-2 pr-4">Days Silent</th>
                <th className="pb-2 pr-4">Value</th>
                <th className="pb-2">Owner</th>
              </tr>
            </thead>
            <tbody>
              {staleDeals.map((d, i) => (
                <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2 pr-4 text-slate-200">{d.company}</td>
                  <td className="py-2 pr-4">
                    <Badge variant={d.stage === "Evaluating" ? "amber" : d.stage === "Cold" ? "slate" : "cyan"}>
                      {d.stage}
                    </Badge>
                  </td>
                  <td className="py-2 pr-4">
                    <span className={d.daysSinceContact > 14 ? "text-red-400" : "text-amber-400"}>
                      {d.daysSinceContact}d
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-300">{fmt(d.value)}</td>
                  <td className="py-2 text-slate-400">{d.owner}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
