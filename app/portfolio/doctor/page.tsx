import ComingSoon from "@/components/ComingSoon";

export const metadata = { title: "Portfolio Doctor — Coming soon" };

export default function PortfolioDoctorPage() {
  return (
    <ComingSoon
      kicker="Portfolio Doctor"
      title="Portfolio health checks are coming soon"
    >
      <p>
        Paste in your existing holdings and Rupeya will diagnose concentration,
        valuation and quality risks against its deterministic scores — and suggest what
        to trim or add. Coming in a future release.
      </p>
    </ComingSoon>
  );
}
