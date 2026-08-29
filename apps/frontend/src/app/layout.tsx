import type { Metadata } from "next"
import { Raleway } from "next/font/google"
import { MantineProvider } from '@mantine/core';
import "./globals.css"
import "@mantine/core/styles.css";
import { ClientNavigation } from "@/components/layout/ClientNavigation"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/ErrorBoundary"

const raleway = Raleway({
  subsets: ["latin"],
  variable: "--font-raleway",
})

export const metadata: Metadata = {
  title: "FairMind - Build Fair & Trustworthy AI",
  description: "Evidence-grade AI governance and assurance control plane for scoped evaluation planning, evidence review, and human decisions.",
  keywords: ["AI governance", "bias detection", "ethical AI", "AI compliance", "fairness", "MLOps"],
  authors: [{ name: "FairMind Team" }],
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
  },
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
    title: "FairMind - Build Fair & Trustworthy AI",
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
    title: "FairMind - Build Fair & Trustworthy AI",
    description: "Evidence-grade AI assurance control plane",
    images: ["/logo.png"],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${raleway.variable} font-sans`}>
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
