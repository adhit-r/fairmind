"use client"

import { Home, Plus, History, Settings, HelpCircle, Shield, Brain, FileText, Users, AlertTriangle, Info } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/common/avatar"
import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

// Sidebar taxonomy: Analyze, Monitor, Explain, Govern, Simulate
const analyzeItems = [
  { title: "DASHBOARD", url: "/", icon: Home },
  { title: "BIAS DETECTION", url: "/bias-detection", icon: AlertTriangle },
  { title: "MODEL DNA", url: "/model-dna", icon: Brain },
  { title: "KNOWLEDGE GRAPH", url: "/knowledge-graph", icon: FileText },
  { title: "LLM TESTING", url: "/llm-testing", icon: Brain },
]

const monitorItems = [
  { title: "MONITORING", url: "/monitoring", icon: Shield },
  { title: "ANALYTICS", url: "/analytics", icon: FileText },
  { title: "GEOGRAPHIC BIAS", url: "/geographic-bias", icon: AlertTriangle },
]

const explainItems = [
  { title: "HOW IT WORKS", url: "/how-it-works", icon: Info },
  { title: "AI ETHICS OBSERVATORY", url: "/ai-ethics-observatory", icon: Brain },
  { title: "HELP & SUPPORT", url: "/help", icon: HelpCircle },
]

const governItems = [
  { title: "COMPLIANCE", url: "/compliance", icon: Shield },
  { title: "AUDIT LOGS", url: "/audit-logs", icon: FileText },
  { title: "STAKEHOLDERS", url: "/stakeholders", icon: Users },
  { title: "SETTINGS", url: "/settings", icon: Settings },
]

const simulateItems = [
  { title: "NEW SIMULATION", url: "/simulation", icon: Plus },
  { title: "SIMULATION HISTORY", url: "/simulation-history", icon: History },
  { title: "MODEL INVENTORY", url: "/models", icon: Brain },
  { title: "MODEL UPLOAD", url: "/model-upload", icon: FileText },
]

export function AppSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()

  const renderNavItem = (item: any) => {
    const isActive = pathname === item.url
    return (
      <Link
        key={item.title}
        href={item.url}
        className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100'
            : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
        }`}
      >
        <item.icon className="h-4 w-4" />
        {!isCollapsed && <span>{item.title}</span>}
      </Link>
    )
  }

  const renderSection = (title: string, items: any[], collapsedTitle: string) => (
    <div className="mb-6">
      <h3 className="px-3 mb-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
        {isCollapsed ? collapsedTitle : title}
      </h3>
      <div className="space-y-1">
        {items.map(renderNavItem)}
      </div>
    </div>
  )

  return (
    <aside className={`bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-blue-600 text-white font-bold">
            <span className="text-sm">FM</span>
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-lg font-bold text-gray-900 dark:text-white">FAIRMIND</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">AI.GOVERNANCE.PLATFORM</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-6">
        {renderSection("ANALYZE", analyzeItems, "ANZ")}
        {renderSection("MONITOR", monitorItems, "MON")}
        {renderSection("EXPLAIN", explainItems, "EXP")}
        {renderSection("GOVERN", governItems, "GOV")}
        {renderSection("SIMULATE", simulateItems, "SIM")}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src="/placeholder.svg?height=32&width=32" />
            <AvatarFallback className="text-xs font-bold">JD</AvatarFallback>
          </Avatar>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-medium text-gray-900 dark:text-white">JOHN DOE</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">Admin</span>
            </div>
          )}
        </div>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute top-4 right-2 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
    </aside>
  )
} 