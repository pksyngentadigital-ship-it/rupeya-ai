// Rupeya.ai — Button
// Mirrors prototype `.btn` with three variants and a size modifier.
// Renders as <button> by default; pass `as="a"` + `href` to render a link.

import Link from "next/link";
import { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "soft";
type Size = "md" | "lg";

interface CommonProps {
  children: ReactNode;
  variant?: Variant;
  size?: Size;
  className?: string;
}

interface ButtonProps
  extends CommonProps,
    Omit<ButtonHTMLAttributes<HTMLButtonElement>, keyof CommonProps> {
  as?: "button";
  href?: never;
}

interface AnchorProps extends CommonProps {
  as: "a";
  href: string;
}

type Props = ButtonProps | AnchorProps;

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-accent text-[#03110A] hover:bg-[#14b076] border border-transparent",
  ghost:
    "bg-transparent text-text border border-borderStrong hover:bg-surface",
  soft: "bg-surfaceAlt text-text border border-transparent hover:bg-border",
};

const SIZE_CLASSES: Record<Size, string> = {
  md: "px-4 py-2.5 text-[14.5px]",
  lg: "px-5 py-3.5 text-[16px]",
};

export default function Button(props: Props) {
  const { children, variant = "primary", size = "md", className = "" } = props;

  const base =
    "inline-flex items-center justify-center gap-2 rounded font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60";
  const cls = `${base} ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`;

  if (props.as === "a") {
    return (
      <Link href={props.href} className={cls}>
        {children}
      </Link>
    );
  }

  const { as: _as, ...rest } = props as ButtonProps;
  return (
    <button {...rest} className={cls}>
      {children}
    </button>
  );
}
