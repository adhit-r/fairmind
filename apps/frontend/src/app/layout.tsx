import type { Metadata, Viewport } from "next"
import { MantineProvider } from '@mantine/core';
import "./globals.css"
import "@mantine/core/styles.css";
import { ClientNavigation } from "@/components/layout/ClientNavigation"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/ErrorBoundary"

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:1111"),
  title: "FairMind P0 Alpha | Evidence Before Assurance",
  description: "Evidence-grade AI governance and assurance control plane for scoped evaluation planning, evidence review, and human decisions.",
  keywords: ["AI governance", "assurance evidence", "evidence provenance", "human review", "model governance"],
  authors: [{ name: "FairMind Team" }],
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "32x32", type: "image/png" },
      { url: "/logo.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  openGraph: {
    title: "FairMind P0 Alpha | Evidence Before Assurance",
    description: "Plan AI evaluations and review scoped evidence without unsupported execution or compliance claims.",
    type: "website",
    images: [
      {
        url: "/logo.png",
        width: 512,
        height: 512,
        alt: "FairMind Logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "FairMind P0 Alpha | Evidence Before Assurance",
    description: "Internal, default-off evidence-control-plane foundation",
    images: ["/logo.png"],
  },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body className="font-sans">
        <MantineProvider>
          <ErrorBoundary>
            <ClientNavigation>{children}</ClientNavigation>
            <Toaster />
          </ErrorBoundary>
        </MantineProvider>
      </body>
    </html>
  )
}
