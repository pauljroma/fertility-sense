"use client";

import { Card, Badge, KPICard, SectionHeading } from "@/components/ui";
import {
  executiveFocus,
  executiveKPIs,
  weeklyActions,
  competitiveAlerts,
} from "@/data/mock-data";
import { AlertTriangle, ArrowRight, Eye } from "lucide-react";

export function ExecutiveView() {
  return (
    <div className="space-y-6">
      {/* Executive Focus Callout */}
      <div className="rounded-lg bg-gradient-to-r from-amber-900/40 via-amber-800/20 to-slate-800/40 border border-amber-700/30 p-5">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h2 className="text-base font-semibold text-slate-100 mb-2">
              {executiveFocus.headline}
            </h2>
            <div className="flex flex-wrap gap-2">
              {executiveFocus.badges.map((b) => (
                <Badge key={b.label} variant={b.variant}>
                  {b.label}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Scorecard */}
      <div>
        <SectionHeading>KPI Scorecard</SectionHeading>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {executiveKPIs.map((kpi) => (
            <KPICard
              key={kpi.label}
              value={kpi.value}
              label={kpi.label}
              trend={kpi.trend}
              target={kpi.target}
            />
          ))}
        </div>
      </div>

      {/* This Week's Actions */}
      <div>
        <SectionHeading>This Week&apos;s Actions</SectionHeading>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {weeklyActions.map((action) => (
            <Card key={action.title} padding="md" interactive>
              <div className="flex items-start gap-3">
                <ArrowRight className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    {action.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    {action.detail}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Competitive Watch */}
      <div>
        <SectionHeading>Competitive Watch</SectionHeading>
        <Card padding="md">
          <ul className="space-y-2">
            {competitiveAlerts.map((alert) => (
              <li key={alert.text} className="flex items-center gap-2 text-sm">
                <Eye className="h-3.5 w-3.5 text-slate-500 flex-shrink-0" />
                <span className="text-slate-300">{alert.text}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
