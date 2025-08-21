import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import "../styles/accessibility.css"
import { AuthProvider } from "@/contexts/auth-context"
import { MainLayout } from "@/components/core/layout/main-layout"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Fairmind - AI Governance Platform",
  description: "Comprehensive AI governance, bias detection, and compliance platform for responsible AI development.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="neo-base">
      <body className={`${inter.className} min-h-screen bg-gray-50`}>
        <AuthProvider>
          <MainLayout>
            {children}
          </MainLayout>
        </AuthProvider>
      </body>
    </html>
  )
}
