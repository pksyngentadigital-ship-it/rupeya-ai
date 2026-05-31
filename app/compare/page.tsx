import ComingSoon from "@/components/ComingSoon";

export const metadata = { title: "Compare — Coming soon" };

export default function ComparePage() {
  return (
    <ComingSoon kicker="Compare" title="Side-by-side stock comparison is coming soon">
      <p>
        Put two or three PSX names head-to-head across all four pillars, valuation and
        margin of safety. For now, open any stock from the Signal List to see its full
        score breakdown.
      </p>
    </ComingSoon>
  );
}
