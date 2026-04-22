"use client";

import { Card, Badge, SectionHeading, ProgressBar } from "@/components/ui";
import { agentStatuses } from "@/data/mock-data";

const statusVariant: Record<string, "emerald" | "blue" | "red"> = {
  running: "emerald",
  idle: "blue",
  error: "red",
};

export function AgentsView() {
  return (
    <div className="space-y-6">
      <SectionHeading>Agent Fleet</SectionHeading>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agentStatuses.map((agent) => (
          <Card key={agent.name} padding="lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-200">{agent.name}</h3>
              <Badge variant={statusVariant[agent.status]}>{agent.status}</Badge>
            </div>

            <p className="text-xs text-slate-400 mb-4">{agent.description}</p>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Success Rate</span>
                <span className="text-slate-200 font-mono">{agent.successRate}%</span>
              </div>
              <ProgressBar
                value={agent.successRate}
                color={agent.successRate >= 95 ? "emerald" : agent.successRate >= 80 ? "amber" : "red"}
                size="sm"
              />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500">Runs today</span>
                <div className="text-slate-200 font-mono">{agent.runsToday}</div>
              </div>
              <div>
                <span className="text-slate-500">Last run</span>
                <div className="text-slate-300">
                  {new Date(agent.lastRun).toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500">Next run</span>
                <div className="text-slate-300">
                  {new Date(agent.nextRun).toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
