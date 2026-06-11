import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexusAI — Autonomous Agent OS",
  description: "Set the goal. Agents handle the rest.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="bg-nexus-bg text-gray-800">
      <body className="min-h-screen antialiased bg-nexus-bg text-gray-800">{children}</body>
    </html>
  );
}
