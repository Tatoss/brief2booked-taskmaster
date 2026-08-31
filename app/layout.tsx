import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "https://brief2booked-147279859950.africa-south1.run.app"),
  title: "Brief2Booked — Autonomous Freelance Operations",
  description: "An event-driven Taskmaster agent that turns client enquiries into qualified, proposal-ready and scheduled opportunities.",
  openGraph: {
    title: "Brief2Booked",
    description: "Autonomous freelance operations",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "Brief2Booked autonomous workflow" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Brief2Booked",
    description: "Autonomous freelance operations",
    images: ["/og.png"],
  },
  other: { "codex-preview": "development" },
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className="antialiased">{children}</body></html>;
}
