import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import "../styles/accessibility.css"
import { AuthProvider } from "@/contexts/auth-context"
import { MainLayout } from "@/components/core/layout/main-layout"
import { ErrorBoundary } from "@/components/ui/common/error-boundary"
import { AccessibilityProvider } from "@/components/ui/common/accessibility"
import { SkipToMainContent } from "@/components/ui/common/accessibility"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Fairmind - AI Governance Platform",
  description: "Comprehensive AI governance, bias detection, and compliance platform for responsible AI development.",
  viewport: "width=device-width, initial-scale=1, maximum-scale=5",
  themeColor: "#3B82F6",
  manifest: "/manifest.json",
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="neo-base">
      <head>
        <meta name="color-scheme" content="light dark" />
        <meta name="supported-color-schemes" content="light dark" />
      </head>
      <body className={`${inter.className} min-h-screen bg-gray-50 dark:bg-gray-900`}>
        <SkipToMainContent />
        <ErrorBoundary showRetry showHome showBack>
          <AccessibilityProvider>
            <AuthProvider>
              <MainLayout>
                <main id="main-content">
                  {children}
                </main>
              </MainLayout>
            </AuthProvider>
          </AccessibilityProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
