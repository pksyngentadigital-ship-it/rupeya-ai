// Rupeya.ai — Card
// Mirrors prototype `.card` (and `.card-hl` highlighted variant).
// All cards use surface bg, border, lg radius, 22px padding.

import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  highlighted?: boolean;
  className?: string;
}

export default function Card({
  children,
  highlighted = false,
  className = "",
}: CardProps) {
  const base = "rounded-lg border p-[22px]";
  const variant = highlighted
    ? "border-accent bg-gradient-to-b from-accent/[0.06] to-transparent bg-surface"
    : "border-border bg-surface";

  return <div className={`${base} ${variant} ${className}`}>{children}</div>;
}

/** Optional muted card title — matches prototype `.card-title`. */
export function CardTitle({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`text-[15px] font-semibold text-textMuted ${className}`}>
      {children}
    </div>
  );
}
