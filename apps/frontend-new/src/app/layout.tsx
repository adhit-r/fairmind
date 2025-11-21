import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ClientNavigation } from "@/components/layout/ClientNavigation"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/ErrorBoundary"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "FairMind - Advanced AI Governance Platform",
  description: "Next-generation AI governance, bias detection, and ethical AI compliance platform",
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
