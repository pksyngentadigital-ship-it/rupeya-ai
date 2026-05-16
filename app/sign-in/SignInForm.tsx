// Rupeya.ai — Sign-in form
// -----------------------------------------------------------
// Two auth paths:
//   • Continue with Google           → OAuth redirect
//   • Email + Password               → explicit "Sign in" / "Create account"
//                                       buttons so the user's intent is
//                                       unambiguous and Supabase errors are
//                                       actionable (no guess-the-flow UX).
//
// First-time password sign-up triggers a confirmation email (Supabase's
// "Confirm email" is enabled). The user clicks the link → /auth/confirm
// → session set → /dashboard.
// -----------------------------------------------------------

"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  signInWithPassword,
  signUpWithPassword,
  signInWithGoogle,
  type AuthResult,
} from "./actions";

export default function SignInForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, startTransition] = useTransition();
  const [feedback, setFeedback] = useState<
    { kind: "info" | "error"; text: string } | null
  >(null);

  function handleResult(res: AuthResult) {
    if (res.ok) {
      if (res.redirectTo) {
        if (res.redirectTo.startsWith("http")) {
          window.location.href = res.redirectTo;
        } else {
          router.push(res.redirectTo);
          router.refresh();
        }
      } else if (res.message) {
        setFeedback({ kind: "info", text: res.message });
      }
    } else {
      setFeedback({ kind: "error", text: res.message });
    }
  }

  function doPasswordSignIn() {
    setFeedback(null);
    const fd = new FormData();
    fd.append("email", email);
    fd.append("password", password);
    startTransition(async () => {
      const res = await signInWithPassword(fd);
      handleResult(res);
    });
  }

  function doPasswordSignUp() {
    setFeedback(null);
    const fd = new FormData();
    fd.append("email", email);
    fd.append("password", password);
    startTransition(async () => {
      const res = await signUpWithPassword(fd);
      handleResult(res);
    });
  }

  function doGoogle() {
    setFeedback(null);
    startTransition(async () => {
      const res = await signInWithGoogle();
      handleResult(res);
    });
  }

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const passwordValid = password.length >= 8;
  const canSubmit = emailValid && passwordValid && !pending;

  return (
    <div className="w-full max-w-md">
      {/* Google */}
      <button
        type="button"
        onClick={doGoogle}
        disabled={pending}
        className="flex w-full items-center justify-center gap-3 rounded border border-borderStrong bg-surface px-4 py-3 font-medium text-text transition-colors hover:bg-surfaceAlt disabled:cursor-not-allowed disabled:opacity-60"
      >
        <GoogleIcon />
        Continue with Google
      </button>

      {/* Divider */}
      <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-wider2 text-textMuted">
        <div className="h-px flex-1 bg-border" />
        <span>or use email</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      {/* Email + password */}
      <label className="block">
        <span className="mb-1.5 block text-xs font-medium uppercase tracking-wider2 text-textMuted">
          Email
        </span>
        <input
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full rounded border border-borderStrong bg-surface px-4 py-3 text-text placeholder:text-textMuted focus:border-accent focus:outline-none"
        />
      </label>

      <label className="mt-4 block">
        <span className="mb-1.5 block text-xs font-medium uppercase tracking-wider2 text-textMuted">
          Password
        </span>
        <input
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          className="w-full rounded border border-borderStrong bg-surface px-4 py-3 text-text placeholder:text-textMuted focus:border-accent focus:outline-none"
        />
      </label>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={doPasswordSignIn}
          disabled={!canSubmit}
          className="rounded bg-accent px-4 py-3 font-semibold text-[#03110A] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {pending ? "…" : "Sign in"}
        </button>
        <button
          type="button"
          onClick={doPasswordSignUp}
          disabled={!canSubmit}
          className="rounded border border-borderStrong bg-surface px-4 py-3 font-semibold text-text transition-colors hover:bg-surfaceAlt disabled:cursor-not-allowed disabled:opacity-50"
        >
          {pending ? "…" : "Create account"}
        </button>
      </div>

      <p className="mt-3 text-xs text-textMuted">
        New here? Click <span className="text-text">Create account</span>.
        Already have one? Click <span className="text-text">Sign in</span>.
        New accounts get a one-time email to confirm the address.
      </p>

      {/* Feedback */}
      {feedback && (
        <div
          role="status"
          className={`mt-5 rounded border px-4 py-3 text-sm ${
            feedback.kind === "error"
              ? "border-danger/40 bg-danger/10 text-danger"
              : "border-accent/40 bg-accentSoft text-accent"
          }`}
        >
          {feedback.text}
        </div>
      )}

      {/* Legal */}
      <p className="mt-6 text-center text-xs text-textMuted">
        By continuing you agree to our{" "}
        <a href="/terms" className="underline hover:text-text">
          Terms
        </a>{" "}
        and{" "}
        <a href="/privacy" className="underline hover:text-text">
          Privacy Policy
        </a>
        .
      </p>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.997 8.997 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.167 6.656 3.58 9 3.58z"
      />
    </svg>
  );
}
