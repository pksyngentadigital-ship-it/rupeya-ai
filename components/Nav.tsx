// Rupeya.ai — Top navigation (auth-aware)
// Sticky, semi-transparent, backdrop-blurred — matches prototype `.nav`.
//
// Behavior:
//   • Logged out → "public" link set (How it works / Pricing / Sample),
//                   plus Sign in + Get started CTAs.
//   • Logged in  → "app" link set (Dashboard / Portfolio / Compare / Ask),
//                   plus user email pill + Sign out.
//
// Mobile uses <MobileMenu> for a proper hamburger sheet (also auth-aware).

import Link from "next/link";
import Logo from "./Logo";
import Container from "./Container";
import MobileMenu from "./MobileMenu";
import SignOutButton from "./SignOutButton";
import { getCurrentUser } from "@/lib/supabase/server";

const PUBLIC_LINKS = [
  { href: "/stocks", label: "Signal List" },
  { href: "/#how", label: "How it works" },
  { href: "/stocks/ATLH", label: "Sample analysis" },
];

const APP_LINKS = [
  { href: "/stocks", label: "Signal List" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/portfolio/build", label: "Portfolio" },
  { href: "/portfolio/doctor", label: "Doctor" },
  { href: "/compare", label: "Compare" },
  { href: "/ask", label: "Ask Rupeya" },
];

export default async function Nav() {
  const user = await getCurrentUser();
  const variant: "public" | "app" = user ? "app" : "public";
  const links = variant === "app" ? APP_LINKS : PUBLIC_LINKS;

  return (
    <nav
      className="sticky top-0 z-50 border-b border-border bg-background/85 backdrop-blur-md"
      aria-label="Primary"
    >
      <Container>
        <div className="relative flex items-center justify-between py-3.5">
          <Logo />

          {/* Desktop link list */}
          <div className="hidden items-center gap-6 text-sm text-textMuted sm:flex">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className="hover:text-text">
                {l.label}
              </Link>
            ))}

            {user ? (
              <div className="flex items-center gap-3 pl-2">
                <span
                  className="max-w-[180px] truncate rounded-full bg-surface px-3 py-1.5 text-xs text-textMuted"
                  title={user.email ?? ""}
                >
                  {user.email}
                </span>
                <SignOutButton />
              </div>
            ) : (
              <>
                <Link
                  href="/sign-in"
                  className="rounded border border-borderStrong px-4 py-2 font-semibold text-text hover:bg-surface"
                >
                  Sign in
                </Link>
                <Link
                  href="/sign-in"
                  className="rounded bg-accent px-4 py-2 font-semibold text-[#03110A] hover:opacity-90"
                >
                  Get started
                </Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <MobileMenu
            variant={variant}
            links={links}
            userEmail={user?.email ?? null}
          />
        </div>
      </Container>
    </nav>
  );
}
