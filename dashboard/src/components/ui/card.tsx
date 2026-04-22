"use client";

import { cn } from "@/lib/cn";

type CardPadding = "sm" | "md" | "lg";

const paddingClasses: Record<CardPadding, string> = {
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

interface CardProps {
  children: React.ReactNode;
  padding?: CardPadding;
  interactive?: boolean;
  className?: string;
}

export function Card({ children, padding = "sm", interactive = false, className }: CardProps) {
  return (
    <div
      className={cn(
        "bg-slate-800/50 border border-slate-700 rounded-lg",
        paddingClasses[padding],
        interactive && "hover:bg-slate-700/30 transition-colors cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );
}
