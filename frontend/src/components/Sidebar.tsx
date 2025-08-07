"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  LayoutDashboard, 
  Shield, 
  Database, 
  AlertTriangle, 
  TestTube, 
  History, 
  Bot, 
  FileCheck, 
  ClipboardList, 
  Users, 
  Settings, 
  HelpCircle,
  Globe,
  Dna,
  FlaskConical,
  Clock,
  Zap,
  Eye
} from "lucide-react"

interface SidebarProps {
  children: React.ReactNode
}

export function Sidebar({ children }: SidebarProps) {
  const pathname = usePathname()

  const navigationItems = [
    {
      title: "MAIN",
      items: [
        {
          href: "/",
          label: "AI Governance Dashboard",
          icon: LayoutDashboard,
          active: pathname === "/",
        },
      ]
    },
    {
      title: "GOVERNANCE",
      items: [
        {
          href: "/models",
          label: "Model Registry",
          icon: Database,
          active: pathname === "/models",
        },
        {
          href: "/compliance",
          label: "Compliance",
          icon: Shield,
          active: pathname === "/compliance",
        },
        {
          href: "/risk-assessment",
          label: "Risk Assessment",
          icon: AlertTriangle,
          active: pathname === "/risk-assessment",
        },
      ]
    },
    {
      title: "TESTING & SIMULATION",
      items: [
        {
          href: "/testing",
          label: "Testing",
          icon: TestTube,
          active: pathname === "/testing",
        },
        {
          href: "/simulation",
          label: "New Simulation",
          icon: Zap,
          active: pathname === "/simulation",
        },
        {
          href: "/simulation-history",
          label: "Simulation History",
          icon: History,
          active: pathname === "/simulation-history",
        },
        {
          href: "/llm-testing",
          label: "LLM Testing",
          icon: Bot,
          active: pathname === "/llm-testing",
        },
      ]
    },
    {
      title: "AI FEATURES",
      items: [
        {
          href: "/geographic-bias",
          label: "Geographic Bias",
          icon: Globe,
          active: pathname === "/geographic-bias",
          badge: "New",
        },
        {
          href: "/ai-dna-profiling",
          label: "AI DNA Profiling",
          icon: Dna,
          active: pathname === "/ai-dna-profiling",
        },
        {
          href: "/ai-genetic-engineering",
          label: "AI Genetic Engineering",
          icon: FlaskConical,
          active: pathname === "/ai-genetic-engineering",
        },
        {
          href: "/ai-time-travel",
          label: "AI Time Travel",
          icon: Clock,
          active: pathname === "/ai-time-travel",
        },
        {
          href: "/ai-circus",
          label: "AI Circus",
          icon: Zap,
          active: pathname === "/ai-circus",
        },
        {
          href: "/ai-ethics-observatory",
          label: "AI Ethics Observatory",
          icon: Eye,
          active: pathname === "/ai-ethics-observatory",
        },
      ]
    },
    {
      title: "SYSTEM",
      items: [
        {
          href: "/audit-logs",
          label: "Audit Logs",
          icon: ClipboardList,
          active: pathname === "/audit-logs",
        },
        {
          href: "/stakeholders",
          label: "Stakeholders",
          icon: Users,
          active: pathname === "/stakeholders",
        },
        {
          href: "/settings",
          label: "Settings",
          icon: Settings,
          active: pathname === "/settings",
        },
        {
          href: "/help",
          label: "Help & Support",
          icon: HelpCircle,
          active: pathname === "/help",
        },
      ]
    },
  ]

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">FM</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">FairMind</h1>
              <p className="text-xs text-gray-500">AI Governance Platform</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-6">
          {navigationItems.map((section) => (
            <div key={section.title}>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                {section.title}
              </h3>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                        item.active
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      <span className="flex-1">{item.label}</span>
                      {item.badge && (
                        <Badge variant="secondary" className="text-xs">
                          {item.badge}
                        </Badge>
                      )}
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 bg-gray-300 rounded-full flex items-center justify-center">
              <span className="text-gray-600 font-medium text-sm">JD</span>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">John Doe</p>
              <p className="text-xs text-gray-500">Administrator</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  )
}
