import ComingSoon from "@/components/ComingSoon";

export const metadata = { title: "Ask Rupeya — Coming soon" };

export default function AskPage() {
  return (
    <ComingSoon kicker="Ask Rupeya" title="Your AI research companion is coming soon">
      <p>
        Ask plain-English questions about any covered PSX stock — “Is FFC still a
        buy?”, “Why is Lucky a TRIM?” — and get a sourced, jargon-free answer grounded
        in the same deterministic scores you see on the Signal List.
      </p>
    </ComingSoon>
  );
}
