'use client'

import React, { useState, useEffect } from 'react'

export default function SimpleHome() {
  const [loading, setLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setLoading(false)
  }, [])

  if (!mounted) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_GOVERNANCE_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">INITIALIZING_DASHBOARD...</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI_GOVERNANCE_DASHBOARD
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">LOADING_DASHBOARD_DATA...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          AI_GOVERNANCE_DASHBOARD
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
        </p>
      </div>

      {/* Simple Content */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-bold text-foreground mb-4">Dashboard Loaded Successfully</h2>
        <p className="text-sm text-muted-foreground">
          This is a simplified version of the dashboard to test if the bootstrap script error is resolved.
        </p>
      </div>
    </div>
  )
}

