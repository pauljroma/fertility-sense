"use client";

import { cn } from "@/lib/cn";

type ProgressBarColor = "blue" | "emerald" | "purple" | "amber" | "red" | "cyan";
type ProgressBarSize = "sm" | "md" | "lg";

const colorClasses: Record<ProgressBarColor, string> = {
  blue: "bg-blue-500",
  emerald: "bg-emerald-500",
  purple: "bg-purple-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
  cyan: "bg-cyan-500",
};

const sizeClasses: Record<ProgressBarSize, string> = {
  sm: "h-2",
  md: "h-3",
  lg: "h-4",
};

interface ProgressBarProps {
  value: number;
  color?: ProgressBarColor;
  size?: ProgressBarSize;
  className?: string;
}

export function ProgressBar({ value, color = "emerald", size = "sm", className }: ProgressBarProps) {
  const clamped = Math.min(Math.max(value, 0), 100);
  return (
    <div className={cn("w-full bg-slate-700 rounded-full overflow-hidden", sizeClasses[size], className)}>
      <div
        className={cn("rounded-full transition-all", sizeClasses[size], colorClasses[color])}
        style={{ width: `${clamped}%` }}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}
