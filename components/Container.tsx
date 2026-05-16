// Rupeya.ai — Page-width container
// Mirrors prototype `.container` (max-width 1100px, 24px horizontal padding).

import { ReactNode } from "react";

interface ContainerProps {
  children: ReactNode;
  className?: string;
}

export default function Container({ children, className = "" }: ContainerProps) {
  return (
    <div className={`mx-auto w-full max-w-page px-6 ${className}`}>
      {children}
    </div>
  );
}
