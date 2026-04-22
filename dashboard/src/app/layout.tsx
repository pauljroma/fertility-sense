import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WIN Fertility \u2014 Growth Intelligence Dashboard",
  description: "B2B demand sensing + pipeline management",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-900 text-slate-200">{children}</body>
    </html>
  );
}
