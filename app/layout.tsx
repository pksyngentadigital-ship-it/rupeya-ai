// Rupeya.ai — Root layout
// Wraps every page with shared chrome (Nav + Footer) and SEO/PWA metadata.
// Nav is auth-aware — it reads the current session server-side and switches
// link sets + CTAs automatically. No per-page variant prop needed.

import type { Metadata, Viewport } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: {
    default: "Rupeya.ai — AI Stock Analyst for PSX",
    template: "%s · Rupeya.ai",
  },
  description:
    "Pakistan's first AI-powered long-term stock analyst. Build a smart, disciplined PSX portfolio — even if you're a complete beginner.",
  applicationName: "Rupeya.ai",
  authors: [{ name: "Rupeya" }],
  keywords: [
    "PSX",
    "Pakistan stock exchange",
    "long-term investing",
    "AI stock analyst",
    "fundamental analysis",
    "Shariah-compliant investing",
    "KSE-100",
  ],
  metadataBase: new URL("https://rupeya-ai.vercel.app"),
  openGraph: {
    title: "Rupeya.ai — AI Stock Analyst for PSX",
    description:
      "AI-powered long-term equity research for Pakistani investors. Built for the PSX. Educational, not advice.",
    url: "https://rupeya-ai.vercel.app",
    siteName: "Rupeya.ai",
    locale: "en_PK",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Rupeya.ai — AI Stock Analyst for PSX",
    description:
      "AI-powered long-term equity research for Pakistani investors. Built for the PSX.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0B0F14",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background font-sans text-text antialiased">
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
