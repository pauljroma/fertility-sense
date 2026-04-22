"use client";

import { useCallback } from "react";
import { cn } from "@/lib/cn";

export interface NavTab {
  id: string;
  label: string;
  icon: string;
}

const tabs: NavTab[] = [
  { id: "pipeline", label: "Pipeline", icon: "\uD83D\uDCCA" },
  { id: "prospects", label: "Prospects", icon: "\uD83D\uDC65" },
  { id: "signals", label: "Signals", icon: "\uD83D\uDCE1" },
  { id: "competitive", label: "Competitive", icon: "\u2694\uFE0F" },
  { id: "sequences", label: "Sequences", icon: "\uD83D\uDCE7" },
  { id: "queue", label: "Queue", icon: "\uD83D\uDCDD" },
  { id: "agents", label: "Agents", icon: "\uD83E\uDD16" },
];

interface NavTabsProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export function NavTabs({ activeTab, onTabChange }: NavTabsProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIndex = tabs.findIndex((t) => t.id === activeTab);
      let nextIndex = currentIndex;

      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextIndex = (currentIndex + 1) % tabs.length;
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      } else if (e.key === "Home") {
        e.preventDefault();
        nextIndex = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        nextIndex = tabs.length - 1;
      }

      if (nextIndex !== currentIndex) {
        onTabChange(tabs[nextIndex].id);
      }
    },
    [activeTab, onTabChange]
  );

  return (
    <nav className="bg-slate-800/40 border-b border-slate-700 px-6" aria-label="Main navigation">
      <div
        className="flex gap-1 max-w-screen-2xl mx-auto overflow-x-auto"
        role="tablist"
        onKeyDown={handleKeyDown}
      >
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={activeTab === t.id}
            aria-controls={`panel-${t.id}`}
            tabIndex={activeTab === t.id ? 0 : -1}
            onClick={() => onTabChange(t.id)}
            className={cn(
              "px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-inset",
              activeTab === t.id
                ? "text-blue-400 border-blue-400"
                : "text-slate-400 border-transparent hover:text-slate-200"
            )}
          >
            <span className="mr-1.5" aria-hidden="true">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
