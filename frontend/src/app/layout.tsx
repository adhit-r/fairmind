import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import "../styles/accessibility.css"
import { AuthProvider } from "@/contexts/auth-context"
import { ThemeProvider } from "@/contexts/theme-context"
import { ThemeToggle } from "@/components/ui/common/theme-toggle"
import { Logo } from "@/components/ui/common/logo"
import { AppSidebar } from "@/components/core/layout/app-sidebar"
import {
  TrendingUp,
  Search,
  TestTube,
  Lock,
  Cog,
  Award,
  BarChart3,
  Brain,
  Target,
  FileText,
  Palette,
  Settings,
  Bell,
  User
} from 'lucide-react'


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
      <body className={`${inter.className} min-h-screen`}>
        <AuthProvider>
          <ThemeProvider>
          <div className="flex min-h-screen">
            {/* Neobrutalism Sidebar */}
            <AppSidebar />

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
              {/* Top Navigation Bar */}
              <header className="border-b-4 shadow-4px-4px-0px-black p-4 neo-card">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <button className="md:hidden neo-button neo-button--secondary text-sm">
                      <Settings className="h-4 w-4 mr-2" />
                      Menu
                    </button>
                    <h2 className="neo-heading neo-heading--md text-xl font-semibold">
                      AI Governance Dashboard
                    </h2>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {/* Notifications */}
                    <button className="neo-button neo-button--info text-sm relative">
                      <Bell className="h-4 w-4" />
                      <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 border-2px-solid-white rounded-full"></span>
                    </button>
                    
                    {/* User Profile */}
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-red-500 rounded-full border-2px-solid-black flex items-center justify-center text-white">
                        <User className="h-4 w-4" />
                      </div>
                      <span className="neo-text neo-text--bold text-sm">User</span>
                    </div>
                  </div>
                </div>
              </header>

              {/* Page Content */}
              <div className="p-6">
                {children}
              </div>
            </main>
                      </div>
            <ThemeToggle />
          </ThemeProvider>
        </AuthProvider>
        </body>
      </html>
    )
  }

// Navigation Item Component
function NavItem({ href, icon, label }: { href: string; icon: string; label: string }) {
  const iconMap: { [key: string]: React.ReactNode } = {
    TrendingUp: <TrendingUp className="h-5 w-5" />,
    Search: <Search className="h-5 w-5" />,
    TestTube: <TestTube className="h-5 w-5" />,
    Lock: <Lock className="h-5 w-5" />,
    Cog: <Cog className="h-5 w-5" />,
    Award: <Award className="h-5 w-5" />,
    BarChart3: <BarChart3 className="h-5 w-5" />,
    Brain: <Brain className="h-5 w-5" />,
    Target: <Target className="h-5 w-5" />,
    FileText: <FileText className="h-5 w-5" />,
    Palette: <Palette className="h-5 w-5" />,
    Settings: <Settings className="h-5 w-5" />
  }

  return (
    <a
      href={href}
      className="block p-3 rounded-lg border-2px-solid-transparent hover:border-2px-solid-black hover:bg-gray-50 transition-all duration-200 neo-text neo-text--bold text-sm"
    >
      <div className="flex items-center space-x-3">
        <span className="text-gray-600">{iconMap[icon] || icon}</span>
        <span>{label}</span>
      </div>
    </a>
  )
}
