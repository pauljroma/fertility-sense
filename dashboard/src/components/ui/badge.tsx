"use client";

import { cn } from "@/lib/cn";

export type BadgeVariant = "blue" | "purple" | "emerald" | "amber" | "red" | "cyan" | "slate";

const variantClasses: Record<BadgeVariant, string> = {
  blue: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  purple: "bg-purple-500/15 text-purple-400 border-purple-500/20",
  emerald: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  amber: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  red: "bg-red-500/15 text-red-400 border-red-500/20",
  cyan: "bg-cyan-500/15 text-cyan-400 border-cyan-500/20",
  slate: "bg-slate-500/15 text-slate-400 border-slate-500/20",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({ children, variant = "blue", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-block text-xs font-semibold px-2 py-0.5 rounded-full border",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
