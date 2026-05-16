// Rupeya.ai — Score bar
// Horizontal track + filled bar. Used for the 4-pillar mini-bars on stock
// pages and verdict cards. Color is auto-tinted by score (or override via tone).

interface ScoreBarProps {
  /** Score on 0-5 scale (matches RupeyaScore pillars). */
  value: number;
  /** Override the auto color. */
  tone?: "accent" | "warn" | "danger";
  /** Optional label shown to the left of the bar. */
  label?: string;
  /** Show the numeric value to the right of the bar. */
  showValue?: boolean;
  className?: string;
}

function autoTone(value: number): "accent" | "warn" | "danger" {
  if (value >= 3.5) return "accent";
  if (value >= 2.5) return "warn";
  return "danger";
}

const FILL_CLASSES = {
  accent: "bg-accent",
  warn: "bg-warn",
  danger: "bg-danger",
};

export default function ScoreBar({
  value,
  tone,
  label,
  showValue = true,
  className = "",
}: ScoreBarProps) {
  const clamped = Math.max(0, Math.min(5, value));
  const pct = (clamped / 5) * 100;
  const t = tone ?? autoTone(clamped);

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {label && (
        <span className="w-32 shrink-0 text-sm text-textMuted">{label}</span>
      )}
      <div
        className="h-2 flex-1 overflow-hidden rounded-full bg-surfaceAlt"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={5}
        aria-label={label}
      >
        <div
          className={`h-full transition-[width] duration-300 ${FILL_CLASSES[t]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showValue && (
        <span className="w-10 shrink-0 text-right text-sm tabular-nums text-text">
          {clamped.toFixed(1)}
        </span>
      )}
    </div>
  );
}
