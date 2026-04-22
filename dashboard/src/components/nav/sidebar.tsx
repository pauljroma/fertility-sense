"use client";

import { useState } from "react";
import {
  BarChart3,
  Target,
  Users,
  TrendingUp,
  Search,
  Radio,
  Database,
  Swords,
  Send,
  Mail,
  ClipboardList,
  Settings,
  Bot,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/cn";

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavSection {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: "Pipeline",
    icon: BarChart3,
    items: [
      { id: "executive", label: "Executive", icon: Target },
      { id: "prospects", label: "Prospects", icon: Users },
      { id: "pipeline", label: "Pipeline", icon: TrendingUp },
    ],
  },
  {
    label: "Intelligence",
    icon: Search,
    items: [
      { id: "signals", label: "Signals", icon: Radio },
      { id: "intelligence", label: "Intelligence", icon: Database },
      { id: "competitive", label: "Competitive", icon: Swords },
    ],
  },
  {
    label: "Outreach",
    icon: Send,
    items: [
      { id: "sequences", label: "Sequences", icon: Mail },
      { id: "queue", label: "Queue", icon: ClipboardList },
    ],
  },
  {
    label: "System",
    icon: Settings,
    items: [{ id: "agents", label: "Agents", icon: Bot }],
  },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col bg-slate-800 border-r border-slate-700 transition-all duration-200 h-full",
        collapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-3 py-4 border-b border-slate-700">
        <span className="text-lg font-bold text-white flex-shrink-0">W</span>
        {!collapsed && (
          <span className="text-sm text-slate-400 truncate">
            WIN Fertility
          </span>
        )}
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto py-2">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label} className="mb-1">
            {/* Section header */}
            {!collapsed && (
              <div className="flex items-center gap-2 px-3 py-2">
                <section.icon className="h-3 w-3 text-slate-500 flex-shrink-0" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  {section.label}
                </span>
              </div>
            )}
            {collapsed && <div className="h-px bg-slate-700 mx-2 my-1" />}

            {/* Section items */}
            {section.items.map((item) => {
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={cn(
                    "flex items-center gap-3 mx-1 rounded px-2 py-1.5 text-sm transition-colors w-[calc(100%-8px)]",
                    active
                      ? "bg-white/10 text-slate-100"
                      : "text-slate-400 hover:bg-white/5 hover:text-slate-200",
                    collapsed && "justify-center"
                  )}
                >
                  <item.icon className="h-4 w-4 flex-shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="mx-2 mb-2 flex h-8 items-center justify-center rounded text-slate-500 hover:bg-white/5 hover:text-slate-300 transition-colors"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>
    </aside>
  );
}
