// Rupeya.ai — Status dot
// 8px round traffic-light indicator. Used in trust band, holdings table,
// and any small inline "is this ok?" affordance.

type DotTone = "good" | "warn" | "bad" | "neutral";

const TONES: Record<DotTone, string> = {
  good: "bg-accent",
  warn: "bg-warn",
  bad: "bg-danger",
  neutral: "bg-textMuted",
};

interface DotProps {
  tone?: DotTone;
  label?: string;
  className?: string;
}

export default function Dot({
  tone = "good",
  label,
  className = "",
}: DotProps) {
  return (
    <span
      role={label ? "img" : undefined}
      aria-label={label}
      className={`inline-block h-2 w-2 rounded-full ${TONES[tone]} ${className}`}
    />
  );
}
