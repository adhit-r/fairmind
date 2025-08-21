"use client"

import { useState, useEffect, createContext, useContext } from 'react'
import { useAuth } from "@/contexts/auth-context"
import { Bell, User, Settings, LogOut, Menu, X } from "lucide-react"
import { modelRegistryService } from "@/lib/model-registry-service"
import { ModernSidebar } from "./modern-sidebar"

// Create context for sidebar state
interface SidebarContextType {
  isCollapsed: boolean
  setIsCollapsed: (collapsed: boolean) => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

export const useSidebar = () => {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider')
  }
  return context
}

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [stats, setStats] = useState({
    totalModels: 0,
    activeModels: 0,
    alerts: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  useEffect(() => {
    const handleSidebarCollapsed = (event: CustomEvent) => {
      setIsCollapsed(event.detail.isCollapsed)
    }

    window.addEventListener('sidebar-collapsed', handleSidebarCollapsed as EventListener)
    
    return () => {
      window.removeEventListener('sidebar-collapsed', handleSidebarCollapsed as EventListener)
    }
  }, [])

  const loadStats = async () => {
    try {
      const orgId = user?.organization_id || 'demo_org'
      const registryStats = await modelRegistryService.getStats(orgId)
      
      setStats({
        totalModels: registryStats.totalModels,
        activeModels: registryStats.activeModels,
        alerts: registryStats.highRiskModels
      })
    } catch (error) {
      console.error('Error loading stats:', error)
      // Fallback to default values
      setStats({
        totalModels: 0,
        activeModels: 0,
        alerts: 0
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed }}>
      <div className="min-h-screen bg-gray-50">
        {/* Modern Sidebar */}
        <ModernSidebar />
        
        {/* Main Content Area */}
        <div className={`transition-all duration-300 ${
          isCollapsed ? 'ml-16' : 'ml-72'
        }`}>
          {/* Header */}
          <header className="bg-white border-b-2 border-black shadow-4px-4px-0px-black sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                {/* Left side - Mobile menu and breadcrumb */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="lg:hidden bg-white border-2 border-black p-2 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
                  >
                    {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                  </button>
                  
                  {/* Breadcrumb */}
                  <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600">
                    <span className="font-medium">FairMind</span>
                    <span>/</span>
                    <span className="text-gray-900">AI Governance</span>
                  </div>
                </div>
                
                {/* Right side - Stats and user info */}
                <div className="flex items-center space-x-4">
                  {/* Quick Stats */}
                  <div className="hidden md:flex items-center space-x-4">
                    <div className="bg-green-100 border-2 border-black px-3 py-1 rounded-lg shadow-2px-2px-0px-black">
                      <span className="text-xs font-bold text-green-800 uppercase">
                        Models: {loading ? "..." : stats.totalModels}
                      </span>
                    </div>
                    <div className="bg-blue-100 border-2 border-black px-3 py-1 rounded-lg shadow-2px-2px-0px-black">
                      <span className="text-xs font-bold text-blue-800 uppercase">
                        Active: {loading ? "..." : stats.activeModels}
                      </span>
                    </div>
                    <div className="bg-orange-100 border-2 border-black px-3 py-1 rounded-lg shadow-2px-2px-0px-black">
                      <span className="text-xs font-bold text-orange-800 uppercase">
                        Alerts: {loading ? "..." : stats.alerts}
                      </span>
                    </div>
                  </div>

                  {/* Notifications */}
                  <button className="bg-white border-2 border-black p-3 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 relative">
                    <Bell className="h-5 w-5 text-gray-600" />
                    {stats.alerts > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        {stats.alerts > 9 ? '9+' : stats.alerts}
                      </span>
                    )}
                  </button>

                  {/* User Menu */}
                  <div className="relative">
                    <button className="bg-white border-2 border-black p-3 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 flex items-center space-x-2">
                      <div className="w-6 h-6 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-medium">
                          {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                        </span>
                      </div>
                      <span className="hidden md:block text-sm font-medium text-gray-700">
                        {user?.full_name || 'User'}
                      </span>
                      <User className="h-4 w-4 text-gray-600" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </SidebarContext.Provider>
  )
}
