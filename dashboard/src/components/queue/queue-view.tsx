"use client";

import { useState, useCallback } from "react";
import {
  ChevronDown,
  ChevronUp,
  Check,
  X,
  Send,
  Mail,
  MessageSquare,
  FileText,
  Share2,
  BookOpen,
} from "lucide-react";
import { Card, Badge, SectionHeading } from "@/components/ui";
import { cn } from "@/lib/cn";
import {
  queueItems as initialItems,
  type QueueItem,
  type QueueItemStatus,
  type QueueChannel,
} from "@/data/mock-data";

const CHANNEL_ICON: Record<QueueChannel, React.ComponentType<{ className?: string }>> = {
  sales_email: Mail,
  linkedin: MessageSquare,
  case_study: BookOpen,
  blog: FileText,
  social: Share2,
};

const CHANNEL_LABEL: Record<QueueChannel, string> = {
  sales_email: "Sales Email",
  linkedin: "LinkedIn",
  case_study: "Case Study",
  blog: "Blog",
  social: "Social",
};

const RISK_VARIANT: Record<string, "emerald" | "amber" | "red"> = {
  low: "emerald",
  medium: "amber",
  high: "red",
};

const STATUS_COLORS: Record<QueueItemStatus, { bg: string; text: string; label: string }> = {
  pending: { bg: "bg-amber-500/15", text: "text-amber-400", label: "Pending" },
  approved: { bg: "bg-emerald-500/15", text: "text-emerald-400", label: "Approved" },
  sent: { bg: "bg-blue-500/15", text: "text-blue-400", label: "Sent" },
  rejected: { bg: "bg-red-500/15", text: "text-red-400", label: "Rejected" },
};

interface Toast {
  id: number;
  message: string;
  variant: "emerald" | "red" | "blue";
}

function HITLReviewCard({
  item,
  onApprove,
  onReject,
  onSend,
}: {
  item: QueueItem;
  onApprove: (id: string) => void;
  onReject: (id: string, reason: string) => void;
  onSend: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const ChannelIcon = CHANNEL_ICON[item.channel];
  const statusInfo = STATUS_COLORS[item.status];

  const handleReject = useCallback(() => {
    onReject(item.id, rejectReason.trim() || "No reason provided");
    setShowRejectInput(false);
    setRejectReason("");
  }, [item.id, onReject, rejectReason]);

  return (
    <div
      className={cn(
        "rounded-xl border transition-colors",
        item.status === "pending"
          ? "border-amber-800/30 bg-amber-950/10"
          : "border-slate-700 bg-slate-800/50"
      )}
    >
      {/* Header */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        <ChannelIcon className="h-4 w-4 flex-shrink-0 text-slate-400" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-slate-200 truncate font-medium">
              {item.title}
            </span>
            <Badge variant={RISK_VARIANT[item.riskTier]}>
              {item.riskTier} risk
            </Badge>
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <span className="text-[11px] text-slate-500">
              {CHANNEL_LABEL[item.channel]}
            </span>
            <span className="text-[11px] text-slate-600">
              {item.evidenceCount} evidence
            </span>
            <span className="text-[11px] text-slate-600">
              {item.targetCompany}
            </span>
          </div>
        </div>

        {/* Status badge */}
        <span
          className={cn(
            "text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full",
            statusInfo.bg,
            statusInfo.text
          )}
        >
          {statusInfo.label}
        </span>

        {expanded ? (
          <ChevronUp className="h-3.5 w-3.5 text-slate-500 flex-shrink-0" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-slate-500 flex-shrink-0" />
        )}
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-700/50 pt-3 space-y-3">
          <div className="rounded-lg bg-black/30 px-3 py-2">
            <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
              {item.body}
            </p>
          </div>

          {item.rejectReason && (
            <div className="text-xs text-red-400 bg-red-900/20 px-3 py-2 rounded-lg">
              Rejected: {item.rejectReason}
            </div>
          )}

          {/* Reject reason textarea */}
          {showRejectInput && (
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason for rejection (optional)"
              rows={2}
              className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600 outline-none focus:border-red-500/60 resize-none"
            />
          )}

          {/* Action buttons */}
          {item.status === "pending" && (
            <div className="flex items-center gap-2 justify-end">
              {showRejectInput ? (
                <>
                  <button
                    onClick={() => {
                      setShowRejectInput(false);
                      setRejectReason("");
                    }}
                    className="px-3 py-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleReject}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-red-900/50 text-red-300 hover:bg-red-900/80 transition-colors"
                  >
                    <X className="h-3 w-3" />
                    Confirm reject
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setShowRejectInput(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs text-red-400 hover:bg-red-900/20 transition-colors"
                  >
                    <X className="h-3 w-3" /> Reject
                  </button>
                  <button
                    onClick={() => onApprove(item.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-green-900/40 text-green-300 hover:bg-green-900/60 transition-colors"
                  >
                    <Check className="h-3 w-3" /> Approve
                  </button>
                </>
              )}
            </div>
          )}

          {/* Send button for approved email items */}
          {item.status === "approved" &&
            (item.channel === "sales_email" || item.channel === "linkedin") && (
              <div className="flex justify-end">
                <button
                  onClick={() => onSend(item.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-blue-900/40 text-blue-300 hover:bg-blue-900/60 transition-colors"
                >
                  <Send className="h-3 w-3" /> Send
                </button>
              </div>
            )}
        </div>
      )}
    </div>
  );
}

export function QueueView() {
  const [items, setItems] = useState<QueueItem[]>(initialItems);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback(
    (message: string, variant: Toast["variant"]) => {
      const id = Date.now();
      setToasts((prev) => [...prev, { id, message, variant }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3000);
    },
    []
  );

  const handleApprove = useCallback(
    (id: string) => {
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: "approved" as const } : item
        )
      );
      addToast("Item approved", "emerald");
    },
    [addToast]
  );

  const handleReject = useCallback(
    (id: string, reason: string) => {
      setItems((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, status: "rejected" as const, rejectReason: reason }
            : item
        )
      );
      addToast("Item rejected", "red");
    },
    [addToast]
  );

  const handleSend = useCallback(
    (id: string) => {
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: "sent" as const } : item
        )
      );
      addToast("Item sent", "blue");
    },
    [addToast]
  );

  const counts: Record<QueueItemStatus, number> = {
    pending: items.filter((i) => i.status === "pending").length,
    approved: items.filter((i) => i.status === "approved").length,
    sent: items.filter((i) => i.status === "sent").length,
    rejected: items.filter((i) => i.status === "rejected").length,
  };

  return (
    <div className="space-y-6">
      <SectionHeading>Outreach Queue</SectionHeading>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {(
          [
            { key: "pending", label: "Pending", variant: "amber" },
            { key: "approved", label: "Approved", variant: "emerald" },
            { key: "sent", label: "Sent", variant: "blue" },
            { key: "rejected", label: "Rejected", variant: "red" },
          ] as const
        ).map(({ key, label, variant }) => (
          <Card key={key} className="text-center">
            <div
              className={cn(
                "text-2xl font-bold",
                variant === "amber" && "text-amber-400",
                variant === "emerald" && "text-emerald-400",
                variant === "blue" && "text-blue-400",
                variant === "red" && "text-red-400"
              )}
            >
              {counts[key]}
            </div>
            <div className="text-xs text-slate-400 mt-1">{label}</div>
          </Card>
        ))}
      </div>

      {/* Review cards */}
      <div className="space-y-3">
        {items.map((item) => (
          <HITLReviewCard
            key={item.id}
            item={item}
            onApprove={handleApprove}
            onReject={handleReject}
            onSend={handleSend}
          />
        ))}
      </div>

      {/* Toast notifications */}
      <div className="fixed bottom-10 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={cn(
              "px-4 py-2 rounded-lg text-xs font-medium shadow-lg animate-in slide-in-from-right",
              toast.variant === "emerald" &&
                "bg-emerald-900/90 text-emerald-300 border border-emerald-700/50",
              toast.variant === "red" &&
                "bg-red-900/90 text-red-300 border border-red-700/50",
              toast.variant === "blue" &&
                "bg-blue-900/90 text-blue-300 border border-blue-700/50"
            )}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}
