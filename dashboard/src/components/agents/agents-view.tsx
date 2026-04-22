"use client";

import { Card, Badge, SectionHeading } from "@/components/ui";
import { agentStatuses, type AgentStatus } from "@/data/mock-data";
import { useApi } from "@/lib/hooks/use-api";

// API agent shape (from /api/agents)
interface LiveAgent {
  name: string;
  role: string;
  tier: string;
  description: string;
  skills: string[];
  enabled: boolean;
}

const roleVariant: Record<string, "blue" | "purple" | "emerald" | "amber"> = {
  analyst: "blue",
  planner: "purple",
  executor: "emerald",
  router: "amber",
};

const tierLabel: Record<string, string> = {
  "claude-haiku-4-5-20251001": "Haiku",
  "claude-sonnet-4-6": "Sonnet",
  "claude-opus-4-6": "Opus",
};

export function AgentsView() {
  const { data: liveAgents, loading, error } = useApi<LiveAgent[]>("/api/agents", 30000);

  // If live API works, show live agent data
  if (liveAgents && !error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <SectionHeading className="mb-0">Agent Fleet</SectionHeading>
          <Badge variant="emerald">Live — {liveAgents.length} agents</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {liveAgents.map((agent) => (
            <Card key={agent.name} padding="lg">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-slate-200">{agent.name}</h3>
                <div className="flex gap-1.5">
                  <Badge variant={roleVariant[agent.role] ?? "slate"}>{agent.role}</Badge>
                  <Badge variant={agent.enabled ? "emerald" : "red"}>
                    {agent.enabled ? "active" : "disabled"}
                  </Badge>
                </div>
              </div>

              <p className="text-xs text-slate-400 mb-4">{agent.description}</p>

              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-slate-500">Model</span>
                <span className="text-slate-200 font-mono">
                  {tierLabel[agent.tier] ?? agent.tier}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Skills</span>
                <span className="text-slate-200 font-mono">{agent.skills.length}</span>
              </div>

              <div className="mt-3 flex flex-wrap gap-1">
                {agent.skills.slice(0, 4).map((skill) => (
                  <span
                    key={skill}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400"
                  >
                    {skill}
                  </span>
                ))}
                {agent.skills.length > 4 && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">
                    +{agent.skills.length - 4} more
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Fallback: mock data while loading or on error
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <SectionHeading className="mb-0">Agent Fleet</SectionHeading>
        {loading ? (
          <Badge variant="slate">Loading...</Badge>
        ) : (
          <Badge variant="amber">Mock data (API unavailable)</Badge>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agentStatuses.map((agent) => (
          <Card key={agent.name} padding="lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-200">{agent.name}</h3>
              <Badge variant={agent.status === "running" ? "emerald" : agent.status === "idle" ? "blue" : "red"}>
                {agent.status}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mb-4">{agent.description}</p>
            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500">Runs today</span>
                <div className="text-slate-200 font-mono">{agent.runsToday}</div>
              </div>
              <div>
                <span className="text-slate-500">Success</span>
                <div className="text-slate-200 font-mono">{agent.successRate}%</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
