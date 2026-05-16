// Rupeya.ai — Logo lockup
// Reused in nav, footer, and any branded card.
// Visual: gradient square with `₨` glyph + "Rupeya" wordmark with green ".ai" suffix.

import Link from "next/link";

interface LogoProps {
  size?: "sm" | "md";
  asLink?: boolean;
}

export default function Logo({ size = "md", asLink = true }: LogoProps) {
  const sq = size === "sm" ? "h-6 w-6 text-[11px]" : "h-7 w-7 text-[13px]";
  const word = size === "sm" ? "text-base" : "text-lg";

  const inner = (
    <span className="flex items-center gap-2 font-bold tracking-tight">
      <span
        aria-hidden="true"
        className={`grid place-items-center rounded-md bg-gradient-to-br from-accent to-[#0AA66C] font-extrabold text-[#03110A] ${sq}`}
      >
        ₨
      </span>
      <span className={word}>
        Rupeya<span className="text-accent">.ai</span>
      </span>
    </span>
  );

  if (!asLink) return inner;
  return (
    <Link href="/" aria-label="Rupeya.ai home">
      {inner}
    </Link>
  );
}
