import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "FairMind Documentation",
    template: "%s | FairMind Documentation",
  },
  description: "Truthful operator and integration documentation for the FairMind P0 assurance control plane.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <header className="site-header">
          <div className="header-inner">
            <Link className="brand" href="/" aria-label="FairMind documentation home">
              <span className="brand-mark" aria-hidden="true">FM</span>
              <span>FairMind <strong>Docs</strong></span>
            </Link>
            <nav className="top-nav" aria-label="Global navigation">
              <Link href="/docs/release-boundary">Release boundary</Link>
              <Link href="/docs">All guides</Link>
              <a href="https://github.com/adhit-r/fairmind">GitHub</a>
            </nav>
          </div>
          <div className="release-strip">
            <span>v2.1.0-alpha.1</span>
            <strong>Internal preview</strong>
            <span>Default-off controls</span>
          </div>
        </header>
        {children}
        <footer className="site-footer">
          <p>FairMind supports assurance evidence workflows. It does not certify legal or regulatory compliance.</p>
          <Link href="/docs/limitations-roadmap">Read limitations</Link>
        </footer>
      </body>
    </html>
  );
}
