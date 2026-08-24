import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RazorGrowth AI — Autonomous Merchant Growth Manager",
  description:
    "Autonomous AI Growth Agent with Razorpay Sandbox Integration, Customer 360, Multi-Agent Loop, Permission Gate, and Live A/B Experimentation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased selection:bg-[#CC785C]/20 selection:text-[#CC785C]">
        {children}
      </body>
    </html>
  );
}
