// Rupeya.ai — Verdict badge
// 5 levels matching blueprint Section 4.7. Color-coded so a glance is enough.
// Always uppercase; never used standalone — paired with a "Research Signal:"
// prefix in critical surfaces (per blueprint Section 4.7 regulatory framing).

export type Verdict = "STRONG BUY" | "BUY" | "HOLD" | "TRIM" | "EXIT";

const STYLES: Record<Verdict, string> = {
  "STRONG BUY": "bg-accent text-[#03110A]",
  BUY: "bg-accentSoft text-accent",
  HOLD: "bg-holdBg text-info",
  TRIM: "bg-trimBg text-warn",
  EXIT: "bg-exitBg text-danger",
};

interface VerdictBadgeProps {
  verdict: Verdict;
  className?: string;
}

export default function VerdictBadge({
  verdict,
  className = "",
}: VerdictBadgeProps) {
  return (
    <span
      className={`inline-block rounded-sm px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider2 ${STYLES[verdict]} ${className}`}
    >
      {verdict}
    </span>
  );
}
