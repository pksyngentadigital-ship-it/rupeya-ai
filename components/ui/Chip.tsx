// Rupeya.ai — Chip / pill
// Generic small pill used for: trust-band claims, Shariah ☪ tag, "Most popular",
// sector labels, and any "category" indicator on a stock or row.

import { ReactNode } from "react";

interface ChipProps {
  children: ReactNode;
  variant?: "default" | "accent";
  className?: string;
}

export default function Chip({
  children,
  variant = "default",
  className = "",
}: ChipProps) {
  const base =
    "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs tracking-wide";
  const variantCls =
    variant === "accent"
      ? "bg-accentSoft text-accent border border-transparent"
      : "bg-surface text-textMuted border border-border";

  return <span className={`${base} ${variantCls} ${className}`}>{children}</span>;
}
