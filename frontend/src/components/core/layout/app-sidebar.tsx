"use client"

import { Home, Plus, History, Settings, HelpCircle, Shield, Brain, FileText, Users, AlertTriangle, Info, ChevronLeft, ChevronRight } from "lucide-react"
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
        className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-semibold transition-all duration-200 border-2 ${
          isActive
            ? 'bg-blue-600 text-white border-black shadow-4px-4px-0px-black'
            : 'text-gray-700 bg-white border-black hover:bg-blue-50 hover:shadow-2px-2px-0px-black'
        }`}
      >
        <item.icon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-gray-600'}`} />
        {!isCollapsed && <span>{item.title}</span>}
      </Link>
    )
  }

  const renderSection = (title: string, items: any[], collapsedTitle: string) => (
    <div className="mb-6">
      <h3 className="px-3 mb-3 text-xs font-black text-gray-600 uppercase tracking-wider border-b-2 border-gray-300 pb-1">
        {isCollapsed ? collapsedTitle : title}
      </h3>
      <div className="space-y-2">
        {items.map(renderNavItem)}
      </div>
    </div>
  )

  return (
    <aside className={`bg-gradient-to-b from-gray-100 to-gray-200 border-r-4 border-black shadow-4px-4px-0px-black transition-all duration-300 flex flex-col ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className="p-4 border-b-4 border-black bg-white">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white font-black border-2 border-black shadow-2px-2px-0px-black">
            <span className="text-sm">FM</span>
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-lg font-black text-gray-900">FAIRMIND</span>
              <span className="text-xs font-bold text-gray-600 uppercase tracking-wider">AI.GOVERNANCE.PLATFORM</span>
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
      <div className="mt-auto p-4 border-t-4 border-black bg-white">
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8 border-2 border-black shadow-2px-2px-0px-black">
            <AvatarImage src="/placeholder.svg?height=32&width=32" />
            <AvatarFallback className="text-xs font-black bg-gradient-to-br from-orange-400 to-red-500 text-white">JD</AvatarFallback>
          </Avatar>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-black text-gray-900">JOHN DOE</span>
              <span className="text-xs font-bold text-gray-600 uppercase">Admin</span>
            </div>
          )}
        </div>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute top-4 right-2 p-2 rounded-md bg-white border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4 text-gray-700" />
        ) : (
          <ChevronLeft className="h-4 w-4 text-gray-700" />
        )}
      </button>
    </aside>
  )
} 