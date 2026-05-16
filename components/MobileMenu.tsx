// Rupeya.ai — Mobile menu (auth-aware)
// Hamburger toggle that drops down a full-width sheet with all nav links
// plus auth state (Sign in / Get started OR user email + Sign out).
// Renders only on small screens (sm:hidden). Closes on route change.

"use client";

import { useState, useEffect, useTransition } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "@/app/auth/actions";

interface NavLink {
  href: string;
  label: string;
}

interface MobileMenuProps {
  variant: "public" | "app";
  links: NavLink[];
  userEmail: string | null;
}

export default function MobileMenu({
  variant,
  links,
  userEmail,
}: MobileMenuProps) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const pathname = usePathname();

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <div className="sm:hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close menu" : "Open menu"}
        aria-expanded={open}
        aria-controls="mobile-menu-panel"
        className="grid h-10 w-10 place-items-center rounded border border-borderStrong text-text hover:bg-surface"
      >
        {open ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
            <line x1="6" y1="6" x2="18" y2="18" />
            <line x1="18" y1="6" x2="6" y2="18" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
            <line x1="4" y1="7" x2="20" y2="7" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="17" x2="20" y2="17" />
          </svg>
        )}
      </button>

      {open && (
        <div
          id="mobile-menu-panel"
          className="absolute left-0 right-0 top-full border-b border-border bg-background shadow-2xl"
        >
          <div className="mx-auto flex max-w-page flex-col gap-1 px-6 py-4">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="rounded px-3 py-3 text-base text-text hover:bg-surface"
                onClick={() => setOpen(false)}
              >
                {l.label}
              </Link>
            ))}

            <div className="mt-2 border-t border-border pt-3">
              {userEmail ? (
                <div className="flex flex-col gap-3">
                  <div
                    className="truncate rounded px-3 py-2 text-xs text-textMuted"
                    title={userEmail}
                  >
                    Signed in as {userEmail}
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setOpen(false);
                      startTransition(() => signOut());
                    }}
                    disabled={pending}
                    className="rounded border border-borderStrong px-4 py-3 text-center font-semibold text-text hover:bg-surface disabled:opacity-60"
                  >
                    {pending ? "Signing out…" : "Sign out"}
                  </button>
                </div>
              ) : variant === "public" ? (
                <div className="flex flex-col gap-2">
                  <Link
                    href="/sign-in"
                    className="rounded border border-borderStrong px-4 py-3 text-center font-semibold text-text hover:bg-surface"
                    onClick={() => setOpen(false)}
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/sign-in"
                    className="rounded bg-accent px-4 py-3 text-center font-semibold text-[#03110A] hover:opacity-90"
                    onClick={() => setOpen(false)}
                  >
                    Get started
                  </Link>
                </div>
              ) : (
                <Link
                  href="/settings"
                  className="block rounded border border-borderStrong px-4 py-3 text-center font-semibold text-text hover:bg-surface"
                  onClick={() => setOpen(false)}
                >
                  Settings
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
