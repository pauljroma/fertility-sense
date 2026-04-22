"use client";

import { Card, Badge, SectionHeading, ProgressBar } from "@/components/ui";
import { emailSequences, recentSends } from "@/data/mock-data";

const statusVariant: Record<string, "emerald" | "blue" | "amber" | "red"> = {
  delivered: "blue",
  opened: "amber",
  replied: "emerald",
  bounced: "red",
};

export function SequencesView() {
  return (
    <div className="space-y-6">
      <SectionHeading>Email Sequences</SectionHeading>

      {/* Sequence Table */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">Active Sequences</SectionHeading>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">Sequence</th>
                <th className="pb-2 pr-4">Buyer Type</th>
                <th className="pb-2 pr-4">Enrolled</th>
                <th className="pb-2 pr-4">Active</th>
                <th className="pb-2 pr-4">Completed</th>
                <th className="pb-2 pr-4">Paused</th>
                <th className="pb-2 pr-4">Open Rate</th>
                <th className="pb-2">Reply Rate</th>
              </tr>
            </thead>
            <tbody>
              {emailSequences.map((seq) => (
                <tr key={seq.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2.5 pr-4 text-slate-200 font-medium">{seq.name}</td>
                  <td className="py-2.5 pr-4">
                    <Badge variant="blue">{seq.buyerType}</Badge>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-300">{seq.enrolled}</td>
                  <td className="py-2.5 pr-4">
                    <span className="text-emerald-400">{seq.active}</span>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-400">{seq.completed}</td>
                  <td className="py-2.5 pr-4 text-slate-500">{seq.paused}</td>
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-mono text-xs w-8">{seq.openRate}%</span>
                      <ProgressBar
                        value={seq.openRate}
                        color={seq.openRate >= 35 ? "emerald" : seq.openRate >= 25 ? "amber" : "red"}
                        size="sm"
                        className="w-16"
                      />
                    </div>
                  </td>
                  <td className="py-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-mono text-xs w-6">{seq.replyRate}%</span>
                      <ProgressBar
                        value={seq.replyRate * 5}
                        color={seq.replyRate >= 10 ? "emerald" : seq.replyRate >= 6 ? "amber" : "red"}
                        size="sm"
                        className="w-12"
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recent Sends */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">Recent Sends</SectionHeading>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">Time</th>
                <th className="pb-2 pr-4">Sequence</th>
                <th className="pb-2 pr-4">Recipient</th>
                <th className="pb-2 pr-4">Subject</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentSends.map((s, i) => (
                <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2 pr-4 text-slate-500 text-xs font-mono whitespace-nowrap">
                    {new Date(s.timestamp).toLocaleTimeString("en-US", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="py-2 pr-4 text-slate-400 text-xs">{s.sequence}</td>
                  <td className="py-2 pr-4 text-slate-300 text-xs font-mono">{s.recipient}</td>
                  <td className="py-2 pr-4 text-slate-200 text-xs max-w-xs truncate">{s.subject}</td>
                  <td className="py-2">
                    <Badge variant={statusVariant[s.status]}>{s.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
