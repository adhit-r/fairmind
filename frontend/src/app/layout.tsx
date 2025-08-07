import type { Metadata } from "next"
import { JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { Sidebar } from "@/components/Sidebar"

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-jetbrains",
})

export const metadata: Metadata = {
  title: "FairMind - Simulated Ethical Sandbox™",
  description: "Test your AI models in synthetic, high-stakes scenarios to uncover ethical risks before deployment.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${jetbrains.className} font-mono`}>
        <Sidebar>
          <div className="h-full overflow-y-auto bg-background p-6">
            {children}
          </div>
        </Sidebar>
      </body>
    </html>
  )
}
