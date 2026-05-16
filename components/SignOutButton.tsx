// Rupeya.ai — Sign-out button
// Tiny client wrapper around the signOut server action so we get a
// pending state and don't ship a full form just for one button.

"use client";

import { useTransition } from "react";
import { signOut } from "@/app/auth/actions";

interface SignOutButtonProps {
  className?: string;
}

export default function SignOutButton({ className = "" }: SignOutButtonProps) {
  const [pending, startTransition] = useTransition();

  return (
    <button
      type="button"
      onClick={() => startTransition(() => signOut())}
      disabled={pending}
      className={`rounded border border-borderStrong px-3 py-2 text-sm text-text transition-colors hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {pending ? "Signing out…" : "Sign out"}
    </button>
  );
}
