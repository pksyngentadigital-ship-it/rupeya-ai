// Rupeya.ai — Kicker pill
// Small uppercase, letter-spaced pill that sits above hero headlines.
// Mirrors prototype `.kicker`.

import { ReactNode } from "react";

interface KickerProps {
  children: ReactNode;
  className?: string;
}

export default function Kicker({ children, className = "" }: KickerProps) {
  return (
    <span
      className={`inline-block rounded-full border border-border bg-surface px-3 py-1.5 text-xs uppercase tracking-kicker text-textMuted ${className}`}
    >
      {children}
    </span>
  );
}
