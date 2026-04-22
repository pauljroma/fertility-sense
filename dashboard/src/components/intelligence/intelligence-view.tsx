"use client";

import { Fragment, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import type { PieLabelRenderProps } from "recharts";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";
import { Card, Badge, SectionHeading, KPICard, ProgressBar } from "@/components/ui";
import type { BadgeVariant } from "@/components/ui";
import { chartTheme } from "@/lib/chart-theme";
import {
  feedSources,
  gradeDistribution,
  coveredTopics,
  uncoveredTopics,
  sampleEvidence,
  intelligenceSummary,
} from "@/data/mock-data";

// ─── Helpers ─────────────────────────────────────────────────────────

const feedTypeColor: Record<string, string> = {
  evidence: "#3b82f6",
  regulatory: "#8b5cf6",
  intelligence: "#f5a623",
  demand: "#06b6d4",
};

const feedTypeBadge: Record<string, BadgeVariant> = {
  evidence: "blue",
  regulatory: "purple",
  intelligence: "amber",
  demand: "cyan",
};

const gradeBadge: Record<string, BadgeVariant> = {
  A: "emerald",
  B: "blue",
  C: "amber",
  D: "slate",
};

const riskBadge: Record<string, BadgeVariant> = {
  red: "red",
  yellow: "amber",
  green: "emerald",
};

// Build the bar chart data for source breakdown
const sourceBarData = feedSources
  .map((f) => ({
    source: f.source.replace(/_/g, " "),
    records: f.recordCount,
    fill: feedTypeColor[f.type],
  }))
  .sort((a, b) => b.records - a.records);

// Map feed sources to the topics they cover (using sample evidence)
const feedTopicMap: Record<string, string[]> = {};
for (const ev of sampleEvidence) {
  if (!feedTopicMap[ev.source]) feedTopicMap[ev.source] = [];
  for (const t of ev.topics) {
    if (!feedTopicMap[ev.source].includes(t)) feedTopicMap[ev.source].push(t);
  }
}

// ─── Component ───────────────────────────────────────────────────────

export function IntelligenceView() {
  const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);
  const [filterSource, setFilterSource] = useState<string>("all");
  const [filterGrade, setFilterGrade] = useState<string>("all");

  const filteredEvidence = sampleEvidence.filter((e) => {
    if (filterSource !== "all" && e.source !== filterSource) return false;
    if (filterGrade !== "all" && e.grade !== filterGrade) return false;
    return true;
  });

  const uniqueSources = [...new Set(sampleEvidence.map((e) => e.source))];
  const uniqueGrades = [...new Set(sampleEvidence.map((e) => e.grade))].sort();

  return (
    <div className="space-y-6">
      <SectionHeading>Intelligence</SectionHeading>

      {/* ── Section 1: KPI Cards ────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard value={String(intelligenceSummary.totalRecords)} label="Total Records" />
        <KPICard value={String(intelligenceSummary.sourcesActive)} label="Sources Active" />
        <KPICard value={`${intelligenceSummary.topicCoveragePct}%`} label="Topic Coverage" />
        <KPICard value={String(intelligenceSummary.feedsRegistered)} label="Feeds Registered" />
      </div>

      {/* ── Section 2: Evidence Source Breakdown ────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bar chart: records by source */}
        <Card padding="md" className="lg:col-span-2">
          <SectionHeading size="sm" as="h3">Records by Source</SectionHeading>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={sourceBarData}
              layout="vertical"
              margin={{ left: 10, right: 20, top: 0, bottom: 0 }}
            >
              <CartesianGrid {...chartTheme.grid} horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: chartTheme.axis.stroke, fontSize: chartTheme.axis.fontSize }}
              />
              <YAxis
                dataKey="source"
                type="category"
                width={130}
                tick={{ fill: chartTheme.axis.stroke, fontSize: 11 }}
              />
              <Tooltip
                contentStyle={chartTheme.tooltip.contentStyle}
                labelStyle={chartTheme.tooltip.labelStyle}
                formatter={(value) => [value, "Records"]}
              />
              <Bar dataKey="records" radius={[0, 4, 4, 0]}>
                {sourceBarData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {/* Legend */}
          <div className="flex flex-wrap gap-4 mt-3">
            {Object.entries(feedTypeColor).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
                {type}
              </div>
            ))}
          </div>
        </Card>

        {/* Pie chart: grade distribution */}
        <Card padding="md">
          <SectionHeading size="sm" as="h3">Grade Distribution</SectionHeading>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={gradeDistribution}
                dataKey="count"
                nameKey="grade"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
                label={({ name, value }: PieLabelRenderProps) => `${name ?? ""}: ${value ?? ""}`}
              >
                {gradeDistribution.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={chartTheme.tooltip.contentStyle}
                labelStyle={chartTheme.tooltip.labelStyle}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {gradeDistribution.map((g) => (
              <div key={g.grade} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: g.color }} />
                Grade {g.grade}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ── Section 3: Topic Coverage ──────────────────────────── */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">Topic Coverage</SectionHeading>
        <div className="flex items-center gap-3 mb-4">
          <ProgressBar
            value={intelligenceSummary.topicCoveragePct}
            color="blue"
            size="md"
            className="flex-1"
          />
          <span className="text-sm text-slate-300 font-mono whitespace-nowrap">
            {intelligenceSummary.topicsCovered} / {intelligenceSummary.topicsTotal}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Covered topics chart */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
              Top Covered Topics
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={coveredTopics}
                layout="vertical"
                margin={{ left: 10, right: 20, top: 0, bottom: 0 }}
              >
                <CartesianGrid {...chartTheme.grid} horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: chartTheme.axis.stroke, fontSize: chartTheme.axis.fontSize }}
                />
                <YAxis
                  dataKey="displayName"
                  type="category"
                  width={140}
                  tick={{ fill: chartTheme.axis.stroke, fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={chartTheme.tooltip.contentStyle}
                  labelStyle={chartTheme.tooltip.labelStyle}
                  formatter={(value) => [value, "Evidence"]}
                />
                <Bar dataKey="evidenceCount" radius={[0, 4, 4, 0]}>
                  {coveredTopics.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={
                        entry.riskTier === "red"
                          ? "#ef4444"
                          : entry.riskTier === "yellow"
                            ? "#f5a623"
                            : "#10b981"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Evidence gaps */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
              Evidence Gaps
            </h4>
            <div className="space-y-2">
              {uncoveredTopics.map((t) => (
                <div
                  key={t.topicId}
                  className={`flex items-center justify-between py-2 px-3 rounded border-l-2 ${
                    t.riskTier === "red"
                      ? "border-l-red-500 bg-red-500/5"
                      : "border-l-slate-600 bg-slate-800/30"
                  }`}
                >
                  <span className="text-sm text-slate-200">{t.displayName}</span>
                  <Badge variant={riskBadge[t.riskTier] || "slate"}>{t.riskTier}</Badge>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Section 4: Feed -> Topic Connections ───────────────── */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">Feed &rarr; Topic Connections</SectionHeading>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {feedSources.map((f) => {
            const topics = feedTopicMap[f.source] || [];
            return (
              <div
                key={f.source}
                className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-200">
                    {f.source.replace(/_/g, " ")}
                  </span>
                  <Badge variant={feedTypeBadge[f.type]}>{f.type}</Badge>
                </div>
                <div className="text-xs text-slate-400 mb-2">
                  {f.recordCount} records &middot; {f.topicsCovered} topics
                  {f.latestDate && (
                    <span className="ml-2 text-slate-500">
                      updated {f.latestDate}
                    </span>
                  )}
                </div>
                {/* Grade breakdown */}
                <div className="flex gap-1.5 mb-2">
                  {Object.entries(f.grades).map(([grade, count]) => (
                    <Badge key={grade} variant={gradeBadge[grade] || "slate"}>
                      {grade}: {count}
                    </Badge>
                  ))}
                </div>
                {/* Topics covered */}
                {topics.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {topics.map((t) => (
                      <span
                        key={t}
                        className="text-[10px] bg-slate-700/50 text-slate-400 px-1.5 py-0.5 rounded"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      {/* ── Section 5: Evidence Explorer ───────────────────────── */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">Evidence Explorer</SectionHeading>

        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="bg-slate-700 text-slate-200 text-sm rounded px-3 py-1.5 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Sources</option>
            {uniqueSources.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          <select
            value={filterGrade}
            onChange={(e) => setFilterGrade(e.target.value)}
            className="bg-slate-700 text-slate-200 text-sm rounded px-3 py-1.5 border border-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Grades</option>
            {uniqueGrades.map((g) => (
              <option key={g} value={g}>
                Grade {g}
              </option>
            ))}
          </select>
        </div>

        {/* Evidence Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-2 w-8"></th>
                <th className="pb-2 pr-4">Grade</th>
                <th className="pb-2 pr-4">Title</th>
                <th className="pb-2 pr-4">Source</th>
                <th className="pb-2 pr-4">Topics</th>
                <th className="pb-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvidence.map((ev) => {
                const isExpanded = expandedEvidence === ev.evidenceId;
                return (
                  <Fragment key={ev.evidenceId}>
                    <tr
                      className="border-b border-slate-700/50 hover:bg-slate-700/20 cursor-pointer"
                      onClick={() =>
                        setExpandedEvidence(isExpanded ? null : ev.evidenceId)
                      }
                    >
                      <td className="py-2 pr-2 text-slate-500">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </td>
                      <td className="py-2 pr-4">
                        <Badge variant={gradeBadge[ev.grade] || "slate"}>{ev.grade}</Badge>
                      </td>
                      <td className="py-2 pr-4 text-slate-200 font-medium max-w-xs truncate">
                        {ev.title}
                      </td>
                      <td className="py-2 pr-4 text-slate-400 font-mono text-xs">
                        {ev.source.replace(/_/g, " ")}
                      </td>
                      <td className="py-2 pr-4">
                        <div className="flex flex-wrap gap-1">
                          {ev.topics.map((t) => (
                            <span
                              key={t}
                              className="text-[10px] bg-slate-700/50 text-slate-400 px-1.5 py-0.5 rounded"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-2 text-slate-400 whitespace-nowrap">
                        {ev.publicationDate || "N/A"}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-slate-800/40">
                        <td colSpan={6} className="py-3 px-4">
                          <div className="space-y-2">
                            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                              Key Findings
                            </h4>
                            <ul className="list-disc list-inside space-y-1">
                              {ev.keyFindings.map((kf, i) => (
                                <li key={i} className="text-sm text-slate-300">
                                  {kf}
                                </li>
                              ))}
                            </ul>
                            {ev.url && (
                              <a
                                href={ev.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mt-1"
                              >
                                <ExternalLink className="h-3 w-3" />
                                View source
                              </a>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
              {filteredEvidence.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No evidence matches the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

