"use client";

import { useState } from "react";
import { Sidebar } from "@/components/nav/sidebar";
import { StatusBar } from "@/components/nav/status-bar";
import { ExecutiveView } from "@/components/executive/executive-view";
import { PipelineView } from "@/components/pipeline/pipeline-view";
import { ProspectsView } from "@/components/prospects/prospects-view";
import { SignalsView } from "@/components/signals/signals-view";
import { CompetitiveView } from "@/components/competitive/competitive-view";
import { SequencesView } from "@/components/sequences/sequences-view";
import { QueueView } from "@/components/queue/queue-view";
import { AgentsView } from "@/components/agents/agents-view";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("executive");

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-y-auto pb-10">
        <div className="max-w-screen-2xl mx-auto p-6">
          {activeTab === "executive" && <ExecutiveView />}
          {activeTab === "pipeline" && <PipelineView />}
          {activeTab === "prospects" && <ProspectsView />}
          {activeTab === "signals" && <SignalsView />}
          {activeTab === "competitive" && <CompetitiveView />}
          {activeTab === "sequences" && <SequencesView />}
          {activeTab === "queue" && <QueueView />}
          {activeTab === "agents" && <AgentsView />}
        </div>
      </main>
      <StatusBar />
    </div>
  );
}
