import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vakil Yantra",
  description: "AI-assisted legal productivity platform for advocates"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
