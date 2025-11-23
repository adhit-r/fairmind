import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ClientNavigation } from "@/components/layout/ClientNavigation"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/ErrorBoundary"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "FairMind - Build Fair & Trustworthy AI",
  description: "Next-generation AI governance, bias detection, and ethical AI compliance platform. Detect bias in ML models, LLMs, and multimodal systems.",
  keywords: ["AI governance", "bias detection", "ethical AI", "AI compliance", "fairness", "MLOps"],
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
    title: "FairMind - Build Fair & Trustworthy AI",
    description: "Detect, analyze, and remediate AI bias with confidence. Comprehensive bias testing for ML, LLMs, and multimodal systems.",
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
    description: "AI Bias Detection & Remediation Platform",
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
      <body className={inter.className}>
        <ErrorBoundary>
          <ClientNavigation>{children}</ClientNavigation>
          <Toaster />
        </ErrorBoundary>
      </body>
    </html>
  )
}
