// Rupeya.ai — Stock-style tag (Dividend / Growth / Both / Cyclical)
// Inline next to a ticker name. Computed deterministically from financials
// per blueprint Section 4.6 — never assigned by an LLM.

export type StockStyle = "dividend" | "growth" | "both" | "cyclical";

const PRESETS: Record<
  StockStyle,
  { label: string; emoji: string; classes: string }
> = {
  dividend: { label: "Dividend", emoji: "💰", classes: "bg-trimBg text-warn" },
  growth: { label: "Growth", emoji: "🚀", classes: "bg-holdBg text-info" },
  both: { label: "Both", emoji: "⚖️", classes: "bg-accentSoft text-accent" },
  cyclical: {
    label: "Cyclical",
    emoji: "🔄",
    classes: "bg-surfaceAlt text-textMuted",
  },
};

interface StyleTagProps {
  style: StockStyle;
  className?: string;
}

export default function StyleTag({ style, className = "" }: StyleTagProps) {
  const { label, emoji, classes } = PRESETS[style];
  return (
    <span
      className={`ml-1.5 inline-flex items-center gap-0.5 rounded-sm px-1.5 py-0.5 text-[10.5px] font-semibold align-middle whitespace-nowrap ${classes} ${className}`}
    >
      <span aria-hidden="true">{emoji}</span> {label}
    </span>
  );
}
