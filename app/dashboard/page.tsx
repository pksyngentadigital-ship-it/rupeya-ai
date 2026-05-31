import ComingSoon from "@/components/ComingSoon";

export const metadata = { title: "Dashboard — Coming soon" };

export default function DashboardPage() {
  return (
    <ComingSoon kicker="Your Dashboard" title="Your portfolio dashboard is coming soon">
      <p>
        Once the AI portfolio builder ships, this is where you’ll track your holdings,
        portfolio health and rebalancing alerts. For now, explore the full research
        signal list.
      </p>
    </ComingSoon>
  );
}
