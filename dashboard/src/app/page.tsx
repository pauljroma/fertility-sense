"use client";

import { useState } from "react";
import { Header, NavTabs } from "@/components/layout";
import { PipelineView } from "@/components/pipeline/pipeline-view";
import { ProspectsView } from "@/components/prospects/prospects-view";
import { SignalsView } from "@/components/signals/signals-view";
import { CompetitiveView } from "@/components/competitive/competitive-view";
import { SequencesView } from "@/components/sequences/sequences-view";
import { QueueView } from "@/components/queue/queue-view";
import { AgentsView } from "@/components/agents/agents-view";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("pipeline");

  return (
    <>
      <Header />
      <NavTabs activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="max-w-screen-2xl mx-auto p-6">
        <div role="tabpanel" id={`panel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
          {activeTab === "pipeline" && <PipelineView />}
          {activeTab === "prospects" && <ProspectsView />}
          {activeTab === "signals" && <SignalsView />}
          {activeTab === "competitive" && <CompetitiveView />}
          {activeTab === "sequences" && <SequencesView />}
          {activeTab === "queue" && <QueueView />}
          {activeTab === "agents" && <AgentsView />}
        </div>
      </main>
    </>
  );
}
