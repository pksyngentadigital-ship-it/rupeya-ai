// Rupeya.ai — Onboarding wizard (client component)
// -----------------------------------------------------------
// 9 questions, one screen at a time. State is local (useState).
// Final screen is a profile summary card; clicking "Build my portfolio"
// persists the profile via the saveInvestorProfile server action and
// redirects to /portfolio/build (which is a stub until Task #17).
// -----------------------------------------------------------

"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Button from "@/components/ui/Button";
import {
  saveInvestorProfile,
  type OnboardingAnswers,
} from "./actions";

type Step =
  | "horizon"
  | "riskReaction"
  | "fundingStyle"
  | "portfolioSize"
  | "monthlyInvestment"
  | "incomeVsGrowth"
  | "experience"
  | "shariahOnly"
  | "goalText";

interface QuestionDef {
  id: Step;
  title: string;
  description?: string;
  type: "single" | "textarea";
  options?: { value: string; label: string }[];
  placeholder?: string;
}

const QUESTIONS: QuestionDef[] = [
  {
    id: "horizon",
    title: "What is your investment horizon?",
    description:
      "How long can you keep this money invested before you'd need it back?",
    type: "single",
    options: [
      { value: "lt1", label: "Less than 1 year" },
      { value: "1to3", label: "1–3 years" },
      { value: "3to5", label: "3–5 years" },
      { value: "5to10", label: "5–10 years" },
      { value: "gt10", label: "More than 10 years" },
    ],
  },
  {
    id: "riskReaction",
    title: "If your portfolio fell 30% in 6 months, what would you do?",
    description: "There are no wrong answers — we use this to size your risk.",
    type: "single",
    options: [
      { value: "sell_all", label: "Sell everything immediately" },
      { value: "sell_some", label: "Sell some to limit further losses" },
      { value: "hold", label: "Hold and wait it out" },
      { value: "buy_more", label: "Buy more at lower prices" },
    ],
  },
  {
    id: "fundingStyle",
    title: "Lump sum or monthly SIP?",
    description: "How will you actually fund this portfolio?",
    type: "single",
    options: [
      { value: "lump_only", label: "Lump sum only" },
      { value: "sip_only", label: "Monthly SIP only" },
      {
        value: "both",
        label: "Both — a starting amount and monthly additions",
      },
    ],
  },
  {
    id: "portfolioSize",
    title: "Approximate portfolio size today?",
    description: "Including any cash you plan to deploy soon.",
    type: "single",
    options: [
      { value: "lt50k", label: "Less than PKR 50,000" },
      { value: "50k_200k", label: "PKR 50,000 – 200,000" },
      { value: "200k_1m", label: "PKR 200,000 – 1,000,000" },
      { value: "1m_5m", label: "PKR 1M – 5M" },
      { value: "gt5m", label: "More than PKR 5M" },
    ],
  },
  {
    id: "monthlyInvestment",
    title: "How much can you invest each month?",
    type: "single",
    options: [
      { value: "lt5k", label: "Less than PKR 5,000" },
      { value: "5k_25k", label: "PKR 5,000 – 25,000" },
      { value: "25k_100k", label: "PKR 25,000 – 100,000" },
      { value: "gt100k", label: "More than PKR 100,000" },
    ],
  },
  {
    id: "incomeVsGrowth",
    title: "Do you prefer dividend income or capital growth?",
    description: "This shapes which kind of PSX companies we pick for you.",
    type: "single",
    options: [
      { value: "dividend", label: "Dividend income (quarterly cash payouts)" },
      { value: "growth", label: "Capital growth (price appreciation over time)" },
      { value: "both", label: "A balance of both" },
    ],
  },
  {
    id: "experience",
    title: "Your PSX experience?",
    type: "single",
    options: [
      { value: "none", label: "First time — never invested before" },
      { value: "1_2y", label: "1–2 years of investing" },
      { value: "3plus", label: "3+ years of investing" },
    ],
  },
  {
    id: "shariahOnly",
    title: "Do you want only Shariah-compliant stocks?",
    description:
      "If yes, Rupeya will only recommend stocks from the KMI All-Share universe — companies that pass AAOIFI Shariah-compliance ratios and avoid prohibited business activities (riba, conventional banking, alcohol, gambling, tobacco, conventional insurance). You can change this anytime in Settings.",
    type: "single",
    options: [
      { value: "yes", label: "Yes — only Shariah-compliant stocks" },
      { value: "no", label: "No — all PSX stocks are fine" },
      { value: "explain_first", label: "I'm not sure — explain it to me first" },
    ],
  },
  {
    id: "goalText",
    title: "In one line — what's the goal of this money?",
    description: "We'll personalize the tone of your reports based on this.",
    type: "textarea",
    placeholder:
      "e.g., House down-payment in 8 years. Or: Build retirement income.",
  },
];

const TOTAL = QUESTIONS.length;

export default function OnboardingWizard() {
  const router = useRouter();
  const [stepIdx, setStepIdx] = useState(0);
  const [answers, setAnswers] = useState<Partial<OnboardingAnswers>>({});
  const [isReview, setIsReview] = useState(false);
  const [pending, startTransition] = useTransition();
  const [saveError, setSaveError] = useState<string | null>(null);

  const q = QUESTIONS[stepIdx];
  const currentAnswer = (answers[q.id] as string | undefined) ?? "";
  const progress = ((stepIdx + 1) / TOTAL) * 100;

  const canProceed =
    q.type === "single"
      ? Boolean(currentAnswer)
      : currentAnswer.trim().length > 0;

  function setAnswer(value: string) {
    setAnswers((prev) => ({ ...prev, [q.id]: value }));
  }

  function next() {
    if (!canProceed) return;
    if (stepIdx < TOTAL - 1) {
      setStepIdx((i) => i + 1);
    } else {
      setIsReview(true);
    }
  }

  function back() {
    if (isReview) {
      setIsReview(false);
      return;
    }
    if (stepIdx > 0) setStepIdx((i) => i - 1);
  }

  function submit() {
    setSaveError(null);
    startTransition(async () => {
      const res = await saveInvestorProfile(answers as OnboardingAnswers);
      if (res.ok) {
        router.push("/portfolio/build");
        router.refresh();
      } else {
        setSaveError(res.message);
      }
    });
  }

  return (
    <div className="mx-auto max-w-2xl">
      {!isReview ? (
        <>
          {/* Progress header */}
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider2 text-textMuted">
              {stepIdx + 1} of {TOTAL}
            </span>
            <span className="text-xs text-textMuted">~3 minutes</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surfaceAlt">
            <div
              className="h-full bg-accent transition-[width] duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Question */}
          <div className="mt-8">
            {q.id === "shariahOnly" && (
              <Chip variant="accent" className="mb-3">
                Faith preference
              </Chip>
            )}
            <h2>{q.title}</h2>
            {q.description && (
              <p className="mt-2 text-textMuted">{q.description}</p>
            )}

            {q.type === "single" && q.options && (
              <div className="mt-6 grid gap-2.5">
                {q.options.map((opt) => {
                  const selected = currentAnswer === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setAnswer(opt.value)}
                      className={`rounded border px-4 py-3.5 text-left text-[15px] transition-colors ${
                        selected
                          ? "border-accent bg-accentSoft text-accent"
                          : "border-borderStrong bg-surface text-text hover:border-accent hover:bg-surfaceAlt"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            )}

            {q.type === "textarea" && (
              <textarea
                value={currentAnswer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={q.placeholder}
                rows={4}
                className="mt-6 w-full rounded border border-borderStrong bg-surface px-4 py-3 text-text placeholder:text-textMuted focus:border-accent focus:outline-none"
              />
            )}
          </div>

          {/* Actions */}
          <div className="mt-8 flex items-center justify-between">
            <button
              type="button"
              onClick={back}
              disabled={stepIdx === 0}
              className="rounded border border-borderStrong px-4 py-2 text-sm text-text transition-opacity hover:bg-surface disabled:invisible"
            >
              ← Back
            </button>
            <Button
              onClick={next}
              disabled={!canProceed}
              variant="primary"
              size="md"
            >
              {stepIdx === TOTAL - 1 ? "See my profile →" : "Next →"}
            </Button>
          </div>
        </>
      ) : (
        <ReviewScreen
          answers={answers as OnboardingAnswers}
          onBack={back}
          onSubmit={submit}
          pending={pending}
          error={saveError}
        />
      )}
    </div>
  );
}

/* -------- Review screen -------- */

function ReviewScreen({
  answers,
  onBack,
  onSubmit,
  pending,
  error,
}: {
  answers: OnboardingAnswers;
  onBack: () => void;
  onSubmit: () => void;
  pending: boolean;
  error: string | null;
}) {
  const horizon = labelOf("horizon", answers.horizon);
  const risk = labelOf("riskReaction", answers.riskReaction);
  const funding = labelOf("fundingStyle", answers.fundingStyle);
  const lump = labelOf("portfolioSize", answers.portfolioSize);
  const monthly = labelOf("monthlyInvestment", answers.monthlyInvestment);
  const income = labelOf("incomeVsGrowth", answers.incomeVsGrowth);
  const exp = labelOf("experience", answers.experience);
  const shariah = labelOf("shariahOnly", answers.shariahOnly);

  return (
    <div>
      <Chip variant="accent">✓ Profile complete</Chip>
      <h2 className="mt-4">Here&apos;s how Rupeya sees you</h2>
      <p className="mt-2 text-textMuted">
        We&apos;ll use this to build your portfolio. You can update it anytime
        in Settings.
      </p>

      <Card className="mt-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <SummaryRow label="Horizon" value={horizon} />
          <SummaryRow label="Risk reaction" value={risk} />
          <SummaryRow label="Funding style" value={funding} />
          <SummaryRow label="Starting capital" value={lump} />
          <SummaryRow label="Monthly SIP" value={monthly} />
          <SummaryRow label="Income vs growth" value={income} />
          <SummaryRow label="Experience" value={exp} />
          <SummaryRow
            label="Faith filter"
            value={shariah}
            accent={answers.shariahOnly === "yes"}
          />
          <div className="sm:col-span-2">
            <SummaryRow label="Goal" value={answers.goalText || "—"} />
          </div>
        </div>
      </Card>

      {error && (
        <div className="mt-4 rounded border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="mt-6 flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBack}
          className="rounded border border-borderStrong px-4 py-2 text-sm text-text hover:bg-surface"
        >
          ← Edit answers
        </button>
        <Button onClick={onSubmit} disabled={pending} variant="primary" size="lg">
          {pending ? "Saving…" : "Build my portfolio →"}
        </Button>
      </div>
      <p className="mt-4 text-center text-xs text-textMuted">
        Takes about 20 seconds. We&apos;ll explain every pick.
      </p>
    </div>
  );
}

function SummaryRow({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div>
      <div className="text-xs text-textMuted">{label}</div>
      <div
        className={`mt-1 font-semibold ${accent ? "text-accent" : "text-text"}`}
      >
        {value}
      </div>
    </div>
  );
}

/* -------- Helpers -------- */

function labelOf(step: Step, value: string | undefined): string {
  if (!value) return "—";
  const q = QUESTIONS.find((x) => x.id === step);
  const opt = q?.options?.find((o) => o.value === value);
  return opt?.label ?? "—";
}
