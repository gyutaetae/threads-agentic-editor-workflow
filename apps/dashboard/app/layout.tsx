import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Threads Workflow Harness",
  description: "Draft, review, learn, and publish @arxiv.ai Threads chains.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
