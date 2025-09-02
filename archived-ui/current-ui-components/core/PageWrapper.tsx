'use client'

import React from 'react'
import { 
  Search, 
  Filter, 
  Sun, 
  RefreshCw,
  Sparkles
} from 'lucide-react'

interface PageWrapperProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  showHeader?: boolean
  showActions?: boolean
}

export function PageWrapper({ 
  children, 
  title, 
  subtitle, 
  showHeader = true,
  showActions = true 
}: PageWrapperProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Modern Header */}
      {showHeader && (
        <div className="bg-white/5 backdrop-blur-xl border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                    <Sparkles className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-white">FairMind</h1>
                    <p className="text-slate-400 text-sm">AI Governance Platform</p>
                  </div>
                </div>
                {title && (
                  <div className="hidden md:flex items-center space-x-1 bg-slate-800/50 rounded-full px-4 py-2">
                    <span className="text-slate-300 text-sm font-medium">{title}</span>
                    {subtitle && (
                      <>
                        <span className="text-slate-500 mx-2">•</span>
                        <span className="text-slate-400 text-sm">{subtitle}</span>
                      </>
                    )}
                  </div>
                )}
              </div>
              
              {showActions && (
                <div className="flex items-center space-x-3">
                  <button className="p-3 text-slate-400 hover:text-white hover:bg-white/5 rounded-xl transition-all duration-300">
                    <Search className="h-5 w-5" />
                  </button>
                  <button className="p-3 text-slate-400 hover:text-white hover:bg-white/5 rounded-xl transition-all duration-300">
                    <Filter className="h-5 w-5" />
                  </button>
                  <button className="p-3 text-slate-400 hover:text-white hover:bg-white/5 rounded-xl transition-all duration-300">
                    <Sun className="h-5 w-5" />
                  </button>
                  <button 
                    onClick={() => window.location.reload()}
                    className="p-3 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-xl transition-all duration-300"
                  >
                    <RefreshCw className="h-5 w-5" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </div>
    </div>
  )
}
