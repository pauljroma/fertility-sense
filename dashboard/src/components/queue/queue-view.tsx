"use client";

import { Card, Badge, SectionHeading } from "@/components/ui";
import { contentQueue } from "@/data/mock-data";

const statusVariant: Record<string, "slate" | "amber" | "blue" | "emerald"> = {
  draft: "slate",
  review: "amber",
  scheduled: "blue",
  published: "emerald",
};

const typeVariant: Record<string, "purple" | "cyan" | "blue" | "amber" | "emerald"> = {
  blog: "cyan",
  case_study: "purple",
  whitepaper: "blue",
  email: "amber",
  social: "emerald",
};

export function QueueView() {
  return (
    <div className="space-y-6">
      <SectionHeading>Content Queue</SectionHeading>

      {/* Status summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {(["draft", "review", "scheduled", "published"] as const).map((status) => {
          const count = contentQueue.filter((c) => c.status === status).length;
          return (
            <Card key={status} className="text-center">
              <div className="text-2xl font-bold text-slate-200">{count}</div>
              <div className="text-xs text-slate-400 mt-1 capitalize">{status}</div>
            </Card>
          );
        })}
      </div>

      {/* Content Table */}
      <Card padding="md">
        <SectionHeading size="sm" as="h3">All Content Items</SectionHeading>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">Title</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Target Buyer</th>
                <th className="pb-2 pr-4">Due Date</th>
                <th className="pb-2">Author</th>
              </tr>
            </thead>
            <tbody>
              {contentQueue.map((c) => (
                <tr key={c.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2.5 pr-4 text-slate-200 font-medium">{c.title}</td>
                  <td className="py-2.5 pr-4">
                    <Badge variant={typeVariant[c.type]}>{c.type.replace("_", " ")}</Badge>
                  </td>
                  <td className="py-2.5 pr-4">
                    <Badge variant={statusVariant[c.status]}>{c.status}</Badge>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-400 text-xs">{c.targetBuyer}</td>
                  <td className="py-2.5 pr-4 text-slate-400 text-xs">{c.dueDate}</td>
                  <td className="py-2.5 text-slate-500 text-xs">{c.author}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
