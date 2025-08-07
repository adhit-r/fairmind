import type { Metadata } from "next"
import { JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { Sidebar } from "@/components/Sidebar"
import { AuthProvider } from "@/contexts/auth-context"
import { ProtectedRoute } from "@/components/protected-route"

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
        <AuthProvider>
          <ProtectedRoute>
            <Sidebar>
              <div className="h-full overflow-y-auto bg-background p-6">
                {children}
              </div>
            </Sidebar>
          </ProtectedRoute>
        </AuthProvider>
      </body>
    </html>
  )
}
