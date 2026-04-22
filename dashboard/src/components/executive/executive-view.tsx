"use client";

import { useState } from "react";
import { Card, Badge, KPICard, SectionHeading } from "@/components/ui";
import {
  executiveFocus,
  executiveKPIs,
  weeklyActions,
  competitiveAlerts,
  type ActionItem,
} from "@/data/mock-data";
import {
  AlertTriangle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Eye,
  Mail,
  Phone,
  User,
  Building,
  Clock,
  DollarSign,
  CheckCircle2,
  Circle,
  AlertCircle,
  Send,
} from "lucide-react";

const priorityVariant: Record<string, "red" | "amber" | "blue"> = {
  high: "red",
  medium: "amber",
  low: "blue",
};

const typeIcon: Record<string, typeof ArrowRight> = {
  followup: User,
  sequence: Mail,
  regulatory: AlertTriangle,
  competitive: Eye,
  new_prospect: Building,
};

const stepIcon: Record<string, typeof Circle> = {
  pending: Circle,
  done: CheckCircle2,
  overdue: AlertCircle,
};

const stepColor: Record<string, string> = {
  pending: "text-slate-500",
  done: "text-emerald-400",
  overdue: "text-red-400",
};

function ActionDrillDown({ action }: { action: ActionItem }) {
  const p = action.prospect;

  return (
    <div className="mt-4 space-y-4 border-t border-slate-700 pt-4">
      {/* Prospect card (if applicable) */}
      {p && (
        <div className="bg-slate-800/80 rounded-lg p-4 border border-slate-600/50">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-blue-400" />
              <span className="text-sm font-semibold text-slate-200">{p.name}</span>
              <Badge variant="blue">{p.buyerType}</Badge>
            </div>
            <Badge variant={p.dealStage === "Evaluating" ? "amber" : p.dealStage === "Warm" ? "cyan" : "slate"}>
              {p.dealStage}
            </Badge>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <Building className="h-3 w-3 text-slate-500" />
              <span className="text-slate-400">{p.company}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Mail className="h-3 w-3 text-slate-500" />
              <span className="text-slate-400">{p.email}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign className="h-3 w-3 text-slate-500" />
              <span className="text-slate-200 font-mono">{p.dealValue}</span>
            </div>
            {p.daysSilent != null && (
              <div className="flex items-center gap-1.5">
                <Clock className="h-3 w-3 text-slate-500" />
                <span className={p.daysSilent > 10 ? "text-red-400" : "text-slate-400"}>
                  {p.daysSilent}d silent
                </span>
              </div>
            )}
          </div>

          {p.currentSequence && (
            <div className="mt-2 text-xs text-slate-500">
              Sequence: <span className="text-slate-300">{p.currentSequence}</span> step{" "}
              <span className="text-slate-300">{p.sequenceStep}</span>
            </div>
          )}
        </div>
      )}

      {/* Context */}
      <div>
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
          Context
        </h4>
        <p className="text-xs text-slate-300 leading-relaxed">{action.context}</p>
      </div>

      {/* Action steps */}
      <div>
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
          Action Steps
        </h4>
        <div className="space-y-2">
          {action.steps.map((s, i) => {
            const Icon = stepIcon[s.status];
            return (
              <div key={i} className="flex items-start gap-2.5">
                <Icon className={`h-4 w-4 flex-shrink-0 mt-0.5 ${stepColor[s.status]}`} />
                <span
                  className={`text-xs ${
                    s.status === "done"
                      ? "text-slate-500 line-through"
                      : s.status === "overdue"
                      ? "text-red-300"
                      : "text-slate-300"
                  }`}
                >
                  {s.step}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Timeline + Impact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-slate-700/30 rounded-lg p-3">
          <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
            Timeline
          </h4>
          <p className="text-xs text-amber-300">{action.timeline}</p>
        </div>
        <div className="bg-slate-700/30 rounded-lg p-3">
          <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">
            Impact
          </h4>
          <p className="text-xs text-emerald-300">{action.impact}</p>
        </div>
      </div>

      {/* Quick actions */}
      <div className="flex gap-2">
        {p && (
          <>
            <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-lg hover:bg-blue-600/30 transition-colors">
              <Send className="h-3 w-3" />
              Send Follow-up
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-600/20 text-slate-300 border border-slate-500/30 rounded-lg hover:bg-slate-600/30 transition-colors">
              <Phone className="h-3 w-3" />
              Schedule Call
            </button>
          </>
        )}
        {action.type === "regulatory" && (
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-amber-600/20 text-amber-400 border border-amber-500/30 rounded-lg hover:bg-amber-600/30 transition-colors">
            <Building className="h-3 w-3" />
            Start Prospecting
          </button>
        )}
      </div>
    </div>
  );
}

export function ExecutiveView() {
  const [expandedAction, setExpandedAction] = useState<number | null>(null);

  const toggleAction = (index: number) => {
    setExpandedAction(expandedAction === index ? null : index);
  };

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

      {/* This Week's Actions — with drill-down */}
      <div>
        <SectionHeading>This Week&apos;s Actions</SectionHeading>
        <div className="space-y-3">
          {weeklyActions.map((action, index) => {
            const isExpanded = expandedAction === index;
            const TypeIcon = typeIcon[action.type] ?? ArrowRight;
            const pending = action.steps.filter((s) => s.status === "pending").length;
            const overdue = action.steps.filter((s) => s.status === "overdue").length;
            const done = action.steps.filter((s) => s.status === "done").length;

            return (
              <Card key={index} padding="md">
                <button
                  onClick={() => toggleAction(index)}
                  className="w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-inset rounded"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <TypeIcon className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-sm font-semibold text-slate-200">
                            {action.title}
                          </h3>
                          <Badge variant={priorityVariant[action.priority]}>
                            {action.priority}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">{action.detail}</p>
                        <div className="flex gap-3 mt-2 text-[10px]">
                          {done > 0 && (
                            <span className="text-emerald-400">{done} done</span>
                          )}
                          {pending > 0 && (
                            <span className="text-slate-400">{pending} pending</span>
                          )}
                          {overdue > 0 && (
                            <span className="text-red-400">{overdue} overdue</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0 ml-3">
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-slate-500" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-slate-500" />
                      )}
                    </div>
                  </div>
                </button>

                {isExpanded && <ActionDrillDown action={action} />}
              </Card>
            );
          })}
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
