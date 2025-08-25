import type { Metadata } from "next"
import { JetBrains_Mono } from "next/font/google"
import "../globals.css"

export const metadata: Metadata = {
  title: "FairMind - Authentication",
  description: "Sign in to FairMind AI Governance Platform",
}

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-jetbrains",
})

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${jetbrains.className} font-mono`}>{children}</body>
    </html>
  )
}
