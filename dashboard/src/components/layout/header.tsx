"use client";

import { Badge } from "@/components/ui";

export function Header() {
  return (
    <header className="bg-slate-800/80 border-b border-slate-700 px-6 py-3">
      <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-white">WIN</span>
          <span className="text-sm text-slate-400">Fertility Growth Engine</span>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="emerald">LIVE</Badge>
          <Badge variant="blue">fertility-sense API</Badge>
          <div className="text-xs text-slate-500">
            Last sync: 2 min ago
          </div>
        </div>
      </div>
    </header>
  );
}
