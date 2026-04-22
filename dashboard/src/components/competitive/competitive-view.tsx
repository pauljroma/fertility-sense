"use client";

import { Card, Badge, SectionHeading } from "@/components/ui";
import { competitors } from "@/data/mock-data";

export function CompetitiveView() {
  return (
    <div className="space-y-6">
      <SectionHeading>Competitive Landscape</SectionHeading>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {competitors.map((c) => (
          <Card key={c.name} padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-200">{c.name}</h3>
              <div className="flex gap-2">
                <Badge variant="blue">{c.revenue}</Badge>
                <Badge variant="purple">{c.clients}</Badge>
              </div>
            </div>

            {/* WIN Positioning */}
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 mb-4">
              <div className="text-xs font-semibold text-emerald-400 mb-1">WIN Positioning</div>
              <div className="text-sm text-slate-300">{c.winPositioning}</div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Strengths */}
              <div>
                <div className="text-xs font-semibold text-slate-400 mb-2">Strengths</div>
                <ul className="space-y-1">
                  {c.strengths.map((s, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                      <span className="text-amber-400 mt-0.5 shrink-0">+</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Weaknesses */}
              <div>
                <div className="text-xs font-semibold text-slate-400 mb-2">Weaknesses</div>
                <ul className="space-y-1">
                  {c.weaknesses.map((w, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                      <span className="text-red-400 mt-0.5 shrink-0">-</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recent Moves */}
            <div>
              <div className="text-xs font-semibold text-slate-400 mb-2">Recent Moves</div>
              <div className="flex flex-wrap gap-1.5">
                {c.recentMoves.map((m, i) => (
                  <Badge key={i} variant="slate">{m}</Badge>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
