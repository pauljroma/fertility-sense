"use client";

import { cn } from "@/lib/cn";

type HeadingSize = "sm" | "md" | "lg";

const sizeClasses: Record<HeadingSize, string> = {
  sm: "text-sm font-semibold text-slate-200 mb-3",
  md: "text-lg font-bold text-slate-200 mb-4",
  lg: "text-xl font-bold text-slate-200 mb-5",
};

interface SectionHeadingProps {
  children: React.ReactNode;
  size?: HeadingSize;
  className?: string;
  as?: "h2" | "h3" | "h4";
}

export function SectionHeading({ children, size = "md", className, as: Tag = "h2" }: SectionHeadingProps) {
  return <Tag className={cn(sizeClasses[size], className)}>{children}</Tag>;
}
