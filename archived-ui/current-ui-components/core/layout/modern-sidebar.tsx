"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from "@/contexts/auth-context"
import { 
  Home, 
  Brain, 
  Shield, 
  FileText, 
  Users, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  BarChart3,
  AlertTriangle,
  Database,
  Target,
  Zap,
  Globe,
  Lock,
  Eye,
  Search,
  Plus,
  History,
  HelpCircle,
  Info,
  TrendingUp,
  Activity,
  Cpu,
  Palette,
  Layers,
  GitBranch,
  Clock,
  Star,
  BookOpen,
  ShieldCheck,
  UserCheck,
  Globe2,
  Code,
  TestTube,
  FlaskConical,
  Microscope,
  Atom,
  Network,
  GitCommit,
  GitPullRequest,
  GitMerge,
  GitCompare,
  GitBranchPlus,
  GitCommitHorizontal,
  GitPullRequestClosed,
  GitPullRequestDraft,
  GitPullRequestCreate,

  Dna
} from 'lucide-react'

interface NavItem {
  title: string
  url: string
  icon: any
  description?: string
  badge?: string
  badgeColor?: 'default' | 'success' | 'warning' | 'error' | 'info'
  isNew?: boolean
  isBeta?: boolean
  isPro?: boolean
}

interface NavSection {
  title: string
  items: NavItem[]
  collapsedTitle: string
  description?: string
}

export function ModernSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const pathname = usePathname()
  const { user } = useAuth()

  // Update parent layout when collapsed state changes
  useEffect(() => {
    const event = new CustomEvent('sidebar-collapsed', { detail: { isCollapsed } })
    window.dispatchEvent(event)
  }, [isCollapsed])

  // Navigation sections with modern organization
  const navSections: NavSection[] = [
    {
      title: "OVERVIEW",
      collapsedTitle: "OVW",
      description: "Main dashboard and analytics",
      items: [
        { title: "Dashboard", url: "/", icon: Home, description: "Main overview" },
        { title: "Analytics", url: "/analytics", icon: BarChart3, description: "Performance metrics", badge: "Live", badgeColor: "success" },
        { title: "Activity", url: "/activity", icon: Activity, description: "Recent activity feed" },
      ]
    },
    {
      title: "AI GOVERNANCE",
      collapsedTitle: "GOV",
      description: "Core AI governance features",
      items: [
        { title: "Bias Detection", url: "/bias-detection", icon: AlertTriangle, description: "Detect model bias", badge: "AI", badgeColor: "warning" },
        { title: "Model DNA", url: "/model-dna", icon: Brain, description: "Model lineage tracking", isNew: true },
        { title: "Knowledge Graph", url: "/knowledge-graph", icon: Network, description: "AI knowledge mapping" },
        { title: "Provenance", url: "/provenance", icon: GitBranch, description: "Model provenance", isBeta: true },
      ]
    },
    {
      title: "SECURITY & COMPLIANCE",
      collapsedTitle: "SEC",
      description: "Security and compliance tools",
      items: [
        { title: "Security Testing", url: "/owasp-security", icon: Shield, description: "OWASP security tests", badge: "OWASP", badgeColor: "error" },
        { title: "Compliance", url: "/compliance", icon: ShieldCheck, description: "Regulatory compliance" },
        { title: "Audit Logs", url: "/audit-logs", icon: FileText, description: "Security audit trail" },
        { title: "Geographic Bias", url: "/geographic-bias", icon: Globe2, description: "Regional bias analysis" },
      ]
    },
    {
      title: "MODEL MANAGEMENT",
      collapsedTitle: "MOD",
      description: "Model lifecycle management",
      items: [
        { title: "Model Registry", url: "/model-registry", icon: Database, description: "Model catalog", badge: "24", badgeColor: "info" },
        { title: "Model Upload", url: "/model-upload", icon: Plus, description: "Upload new models" },
        { title: "Model Testing", url: "/llm-testing", icon: TestTube, description: "LLM testing suite" },
        { title: "Model Monitoring", url: "/monitoring", icon: Eye, description: "Real-time monitoring" },
      ]
    },
    {
      title: "SIMULATION & TESTING",
      collapsedTitle: "SIM",
      description: "AI simulation and testing",
      items: [
        { title: "New Simulation", url: "/simulation", icon: FlaskConical, description: "Create simulation", isPro: true },
        { title: "Simulation History", url: "/simulation-history", icon: History, description: "Past simulations" },
        { title: "A/B Testing", url: "/ab-testing", icon: GitCompare, description: "Model comparison" },
        { title: "Performance Testing", url: "/performance-testing", icon: Zap, description: "Performance analysis" },
      ]
    },
    {
      title: "ADVANCED FEATURES",
      collapsedTitle: "ADV",
      description: "Advanced AI governance features",
      items: [
        { title: "AI Ethics Observatory", url: "/ai-ethics-observatory", icon: Atom, description: "Global AI ethics", isPro: true },
        { title: "Genetic Engineering", url: "/ai-genetic-engineering", icon: Dna, description: "AI model evolution" },
        { title: "Time Travel", url: "/ai-time-travel", icon: Clock, description: "Temporal analysis" },
        { title: "AI Circus", url: "/ai-circus", icon: Palette, description: "Creative AI testing" },
      ]
    },
    {
      title: "ADMINISTRATION",
      collapsedTitle: "ADM",
      description: "System administration",
      items: [
        { title: "Users & Teams", url: "/users", icon: Users, description: "User management" },
        { title: "Settings", url: "/settings", icon: Settings, description: "System settings" },
        { title: "Help & Support", url: "/help", icon: HelpCircle, description: "Documentation" },
        { title: "About", url: "/about", icon: Info, description: "System information" },
      ]
    }
  ]

  // Find active section based on current path
  useEffect(() => {
    const currentSection = navSections.find(section =>
      section.items.some(item => item.url === pathname)
    )
    setActiveSection(currentSection?.title || null)
  }, [pathname])

  const renderBadge = (badge: string, color: string = 'default') => {
    const colorClasses = {
      default: 'bg-gray-100 text-gray-800',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      info: 'bg-blue-100 text-blue-800'
    }

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClasses[color as keyof typeof colorClasses]}`}>
        {badge}
      </span>
    )
  }

  const renderNavItem = (item: NavItem) => {
    const isActive = pathname === item.url
    const isInActiveSection = activeSection && navSections.find(s => s.title === activeSection)?.items.includes(item)

    return (
      <Link
        key={item.title}
        href={item.url}
        className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 border-2 ${
          isActive
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white border-black shadow-4px-4px-0px-black'
            : isInActiveSection
            ? 'bg-blue-50 text-blue-900 border-blue-200 hover:bg-blue-100'
            : 'text-gray-700 bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300 hover:shadow-2px-2px-0px-gray-300'
        } ${isCollapsed ? 'justify-center px-2' : ''}`}
        title={isCollapsed ? item.title : undefined}
      >
        {/* Active indicator */}
        {isActive && (
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-600 to-purple-600 rounded-r-full" />
        )}
        
        {/* Icon */}
        <div className={`flex-shrink-0 ${isActive ? 'text-white' : 'text-gray-600 group-hover:text-gray-900'} ${isCollapsed ? 'flex justify-center' : ''}`}>
          <item.icon className="h-4 w-4" />
        </div>
        
        {/* Content */}
        {!isCollapsed && (
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="truncate font-medium">{item.title}</span>
              <div className="flex items-center gap-1">
                {item.isNew && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    NEW
                  </span>
                )}
                {item.isBeta && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                    BETA
                  </span>
                )}
                {item.isPro && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                    PRO
                  </span>
                )}
                {item.badge && renderBadge(item.badge, item.badgeColor)}
              </div>
            </div>
            {item.description && (
              <p className={`text-xs mt-0.5 truncate ${
                isActive ? 'text-blue-100' : 'text-gray-500 group-hover:text-gray-700'
              }`}>
                {item.description}
              </p>
            )}
          </div>
        )}
        
        {/* Badge for collapsed state */}
        {isCollapsed && (item.badge || item.isNew || item.isBeta || item.isPro) && (
          <div className="absolute -top-1 -right-1">
            {item.isNew && (
              <span className="inline-flex items-center justify-center w-3 h-3 rounded-full bg-green-500 text-white text-xs">
                N
              </span>
            )}
            {item.isBeta && (
              <span className="inline-flex items-center justify-center w-3 h-3 rounded-full bg-yellow-500 text-white text-xs">
                B
              </span>
            )}
            {item.isPro && (
              <span className="inline-flex items-center justify-center w-3 h-3 rounded-full bg-purple-500 text-white text-xs">
                P
              </span>
            )}
            {item.badge && !item.isNew && !item.isBeta && !item.isPro && (
              <span className="inline-flex items-center justify-center w-3 h-3 rounded-full bg-blue-500 text-white text-xs">
                {item.badge.length > 1 ? item.badge.charAt(0) : item.badge}
              </span>
            )}
          </div>
        )}
      </Link>
    )
  }

  const renderSection = (section: NavSection) => (
    <div key={section.title} className="mb-6">
      {/* Section Header */}
      <div className={`px-3 mb-3 ${isCollapsed ? 'text-center' : ''}`}>
        <h3 className={`font-bold uppercase tracking-wider border-b-2 pb-1 ${
          isCollapsed 
            ? 'text-xs text-gray-600 border-gray-300 text-center' 
            : 'text-sm text-gray-700 border-gray-300'
        }`}>
          {isCollapsed ? section.collapsedTitle : section.title}
        </h3>
        {!isCollapsed && section.description && (
          <p className="text-xs text-gray-500 mt-1">{section.description}</p>
        )}
      </div>
      
      {/* Section Items */}
      <div className="space-y-1">
        {section.items.map(renderNavItem)}
      </div>
    </div>
  )

  return (
    <aside className={`fixed left-0 top-0 h-full bg-white border-r-2 border-gray-200 shadow-lg transition-all duration-300 z-50 ${
      isCollapsed ? 'w-16' : 'w-72'
    }`}>
      {/* Header */}
      <div className="p-4 border-b-2 border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 text-white font-bold border-2 border-black shadow-2px-2px-0px-black">
              <span className="text-sm">FM</span>
            </div>
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="text-lg font-bold text-gray-900">FairMind</span>
                <span className="text-xs text-gray-600 uppercase tracking-wider">AI Governance</span>
              </div>
            )}
          </div>
          
          {/* Collapse Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4 text-gray-600" />
            ) : (
              <ChevronLeft className="h-4 w-4 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* User Info */}
      {!isCollapsed && user && (
        <div className="p-4 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user.full_name?.charAt(0) || user.email?.charAt(0) || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user.full_name || 'User'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user.organization_name || 'Organization'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* User Avatar for collapsed state */}
      {isCollapsed && user && (
        <div className="p-2 border-b border-gray-100 bg-gray-50">
          <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center mx-auto">
            <span className="text-white text-sm font-medium">
              {user.full_name?.charAt(0) || user.email?.charAt(0) || 'U'}
            </span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-6">
        {navSections.map(renderSection)}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        {!isCollapsed ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Version 1.0.0</span>
              <span>Beta</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Star className="h-3 w-3" />
              <span>AI Governance Platform</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="AI Governance Platform">
            <Star className="h-4 w-4 text-gray-400" />
          </div>
        )}
      </div>
    </aside>
  )
}
