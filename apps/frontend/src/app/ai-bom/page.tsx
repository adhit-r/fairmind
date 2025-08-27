'use client'

import React, { useState, useEffect } from 'react'

interface BOMComponent {
  id: string
  name: string
  type: 'model' | 'dataset' | 'framework' | 'library' | 'service' | 'infrastructure'
  version: string
  source: string
  license: string
  licenseType: 'open-source' | 'proprietary' | 'commercial' | 'research'
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  dependencies: string[]
  lastUpdated: string
  maintainer: string
  description: string
  usage: string
  complianceStatus: 'compliant' | 'non-compliant' | 'review' | 'pending'
}

interface BOMDocument {
  id: string
  name: string
  version: string
  createdAt: string
  lastUpdated: string
  totalComponents: number
  riskComponents: number
  complianceScore: number
  licenseCompliance: number
  securityScore: number
  components: BOMComponent[]
}

interface BOMMetrics {
  totalBOMs: number
  activeBOMs: number
  averageCompliance: number
  criticalVulnerabilities: number
  licenseViolations: number
  lastScan: string
  nextReview: string
}

export default function AIBOM() {
  const [loading, setLoading] = useState(true)
  const [boms, setBoms] = useState<BOMDocument[]>([])
  const [metrics, setMetrics] = useState<BOMMetrics>({
    totalBOMs: 0,
    activeBOMs: 0,
    averageCompliance: 0,
    criticalVulnerabilities: 0,
    licenseViolations: 0,
    lastScan: '',
    nextReview: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedRisk, setSelectedRisk] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            AI Bill of Materials
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            AI Component Inventory & Supply Chain Transparency
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading AI BOM...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          AI Bill of Materials
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          AI Component Inventory & Supply Chain Transparency
        </p>
      </div>

      {/* BOM Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">BOM Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Component inventory and supply chain transparency
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">94%</div>
            <span className="text-sm text-muted-foreground font-mono">Average Compliance</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">2</div>
            <div className="text-xs text-muted-foreground font-mono">Total BOMs</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">2</div>
            <div className="text-xs text-muted-foreground font-mono">Active BOMs</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">0</div>
            <div className="text-xs text-muted-foreground font-mono">Critical Vulnerabilities</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">1</div>
            <div className="text-xs text-muted-foreground font-mono">License Violations</div>
          </div>
        </div>
      </div>

      {/* BOM Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Scan</h3>
          <div className="text-sm font-bold text-foreground">2024-01-20 16:30:00</div>
          <p className="text-xs text-muted-foreground font-mono">Comprehensive component scan</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Review</h3>
          <div className="text-sm font-bold text-foreground">2024-02-20</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled BOM review</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Types</option>
            <option value="model">Models</option>
            <option value="dataset">Datasets</option>
            <option value="framework">Frameworks</option>
            <option value="library">Libraries</option>
            <option value="service">Services</option>
            <option value="infrastructure">Infrastructure</option>
          </select>
          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Risk Levels</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Generate New BOM
        </button>
      </div>

      {/* BOM Documents */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Bill of Materials</h2>
        
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📦</div>
            <h3 className="text-lg font-bold text-foreground mb-2">AI Bill of Materials</h3>
            <p className="text-sm text-muted-foreground font-mono">
              Component inventory, dependency tracking, and supply chain transparency
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
