"use client";

import { useState, useMemo } from "react";
import { Card, Badge, SectionHeading, ProgressBar } from "@/components/ui";
import { prospects } from "@/data/mock-data";

type SortKey = "dealScore" | "dealValue" | "lastContact";
type SortDir = "asc" | "desc";

const stageVariant: Record<string, "slate" | "cyan" | "amber" | "purple" | "emerald"> = {
  Cold: "slate",
  Warm: "cyan",
  Evaluating: "amber",
  Negotiating: "purple",
  Won: "emerald",
};

function fmt(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n}`;
}

export function ProspectsView() {
  const [filterStage, setFilterStage] = useState<string>("all");
  const [filterBuyer, setFilterBuyer] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("dealScore");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const stages = ["all", "Cold", "Warm", "Evaluating", "Negotiating", "Won"];
  const buyerTypes = ["all", ...new Set(prospects.map((p) => p.buyerType))];

  const filtered = useMemo(() => {
    let result = [...prospects];
    if (filterStage !== "all") result = result.filter((p) => p.dealStage === filterStage);
    if (filterBuyer !== "all") result = result.filter((p) => p.buyerType === filterBuyer);
    result.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "desc" ? bVal - aVal : aVal - bVal;
      }
      return sortDir === "desc"
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal));
    });
    return result;
  }, [filterStage, filterBuyer, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sortIndicator = (key: SortKey) =>
    sortKey === key ? (sortDir === "desc" ? " \u25BC" : " \u25B2") : "";

  return (
    <div className="space-y-6">
      <SectionHeading>Prospect Pipeline</SectionHeading>

      {/* Filters */}
      <Card padding="sm">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Stage:</span>
            {stages.map((s) => (
              <button
                key={s}
                onClick={() => setFilterStage(s)}
                className={`text-xs px-2 py-1 rounded ${
                  filterStage === s
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {s === "all" ? "All" : s}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Buyer:</span>
            <select
              value={filterBuyer}
              onChange={(e) => setFilterBuyer(e.target.value)}
              className="bg-slate-700 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1"
            >
              {buyerTypes.map((b) => (
                <option key={b} value={b}>
                  {b === "all" ? "All Types" : b}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card padding="md">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">Name</th>
                <th className="pb-2 pr-4">Company</th>
                <th className="pb-2 pr-4">Buyer Type</th>
                <th className="pb-2 pr-4">Stage</th>
                <th className="pb-2 pr-4 cursor-pointer select-none" onClick={() => toggleSort("dealScore")}>
                  Score{sortIndicator("dealScore")}
                </th>
                <th className="pb-2 pr-4 cursor-pointer select-none" onClick={() => toggleSort("dealValue")}>
                  Value{sortIndicator("dealValue")}
                </th>
                <th className="pb-2 pr-4 cursor-pointer select-none" onClick={() => toggleSort("lastContact")}>
                  Last Contact{sortIndicator("lastContact")}
                </th>
                <th className="pb-2">Next Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2.5 pr-4 text-slate-200 font-medium">{p.name}</td>
                  <td className="py-2.5 pr-4 text-slate-300">{p.company}</td>
                  <td className="py-2.5 pr-4">
                    <Badge variant="blue">{p.buyerType}</Badge>
                  </td>
                  <td className="py-2.5 pr-4">
                    <Badge variant={stageVariant[p.dealStage] ?? "slate"}>{p.dealStage}</Badge>
                  </td>
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-mono text-xs w-7">{p.dealScore}</span>
                      <ProgressBar
                        value={p.dealScore}
                        color={p.dealScore >= 80 ? "emerald" : p.dealScore >= 60 ? "amber" : "red"}
                        size="sm"
                        className="w-16"
                      />
                    </div>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-300">{fmt(p.dealValue)}</td>
                  <td className="py-2.5 pr-4 text-slate-400 text-xs">{p.lastContact}</td>
                  <td className="py-2.5 text-slate-400 text-xs">{p.nextAction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center text-slate-500 py-8">No prospects match the current filters.</div>
        )}
      </Card>
    </div>
  );
}
