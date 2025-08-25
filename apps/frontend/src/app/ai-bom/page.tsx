'use client'

import React, { useState, useEffect } from 'react'
import { 
  Plus, 
  FileText, 
  BarChart3, 
  Shield, 
  Settings, 
  Download, 
  Eye, 
  PlusCircle,
  Brain,
  Zap,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'

interface BOMDocument {
  id: string
  name: string
  model_name: string
  created_at: string
  status: 'completed' | 'processing' | 'failed'
  overall_risk_level: 'low' | 'medium' | 'high' | 'critical'
  components_count: number
  vulnerabilities_count: number
  compliance_score: number
}

export default function AIBOMPage() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [bomDocuments, setBomDocuments] = useState<BOMDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBOMDocuments()
  }, [])

  const fetchBOMDocuments = async () => {
    try {
      setLoading(true)
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock data
      const mockDocuments: BOMDocument[] = [
        {
          id: 'bom-1',
          name: 'Credit Risk Model BOM',
          model_name: 'Credit Risk Model v2.1',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          status: 'completed',
          overall_risk_level: 'medium',
          components_count: 45,
          vulnerabilities_count: 3,
          compliance_score: 78
        },
        {
          id: 'bom-2',
          name: 'Fraud Detection BOM',
          model_name: 'Fraud Detection AI',
          created_at: new Date().toISOString(),
          status: 'processing',
          overall_risk_level: 'low',
          components_count: 32,
          vulnerabilities_count: 1,
          compliance_score: 92
        }
      ]
      
      setBomDocuments(mockDocuments)
    } catch (error) {
      console.error('Error fetching BOM documents:', error)
      setError('Failed to load BOM documents')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-400" />
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-400" />
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-400" />
      default:
        return <Clock className="h-5 w-5 text-slate-400" />
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-400'
      case 'medium':
        return 'text-yellow-400'
      case 'high':
        return 'text-orange-400'
      case 'critical':
        return 'text-red-400'
      default:
        return 'text-slate-400'
    }
  }

  const getRiskBgColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-500/10 border-green-500/20'
      case 'medium':
        return 'bg-yellow-500/10 border-yellow-500/20'
      case 'high':
        return 'bg-orange-500/10 border-orange-500/20'
      case 'critical':
        return 'bg-red-500/10 border-red-500/20'
      default:
        return 'bg-slate-500/10 border-slate-500/20'
    }
  }

  if (loading) {
    return (
      <PageWrapper title="AI Bill of Materials" subtitle="AI System Documentation">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-400">Loading BOM documents...</p>
          </div>
        </div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper title="AI Bill of Materials" subtitle="AI System Documentation">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
            <div>
            <h1 className="text-3xl font-bold text-white mb-2">AI Bill of Materials</h1>
            <p className="text-slate-400 text-lg">
                Comprehensive documentation and analysis of AI system components
              </p>
            </div>
          <div className="flex space-x-3">
              <Button 
              icon={Plus}
              onClick={() => setActiveTab('create')}
              >
                Create BOM
              </Button>
            <Button 
              variant="outline"
              icon={Download}
            >
                Export
              </Button>
            </div>
          </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-slate-800/50 rounded-xl p-1 mb-6">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
            { id: 'create', label: 'Create BOM', icon: PlusCircle },
            { id: 'analyze', label: 'Analyze', icon: Brain },
            { id: 'compliance', label: 'Compliance', icon: Shield },
            { id: 'export', label: 'Export', icon: Download }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-500 text-white shadow-lg'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card gradient="red" className="mb-6">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
        </Card>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <>
        {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card hover>
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <FileText className="h-6 w-6 text-white" />
                  </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">{bomDocuments.length}</p>
                  <p className="text-slate-400 text-sm">Total BOMs</p>
                </div>
              </div>
            </Card>

            <Card hover>
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-600 rounded-xl flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-white" />
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">
                      {bomDocuments.filter(bom => bom.overall_risk_level === 'high' || bom.overall_risk_level === 'critical').length}
                    </p>
                  <p className="text-slate-400 text-sm">High Risk</p>
                </div>
              </div>
            </Card>

            <Card hover>
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">
                    {bomDocuments.filter(bom => bom.status === 'completed').length}
                  </p>
                  <p className="text-slate-400 text-sm">Completed</p>
                </div>
              </div>
            </Card>

            <Card hover>
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">
                    {bomDocuments.length > 0 ? Math.round(bomDocuments.reduce((acc, bom) => acc + bom.compliance_score, 0) / bomDocuments.length) : 0}%
                  </p>
                  <p className="text-slate-400 text-sm">Avg Compliance</p>
                </div>
              </div>
            </Card>
          </div>

          {/* BOM Documents */}
          <Card 
            title="BOM Documents"
            icon={<Activity className="h-5 w-5 text-blue-400" />}
          >
            {bomDocuments.length > 0 ? (
              <div className="space-y-4">
                {bomDocuments.map((bom) => (
                  <div key={bom.id} className="bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-all duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center`}>
                          {getStatusIcon(bom.status)}
                        </div>
                        <div>
                          <p className="font-semibold text-white">{bom.name}</p>
                          <p className="text-slate-400 text-sm">{bom.model_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <p className="text-sm text-slate-400">Components</p>
                          <p className="text-sm font-semibold text-white">{bom.components_count}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-400">Vulnerabilities</p>
                          <p className="text-sm font-semibold text-red-400">{bom.vulnerabilities_count}</p>
                        </div>
                        <div className={`px-3 py-1 rounded-lg border text-xs font-medium ${getRiskBgColor(bom.overall_risk_level)}`}>
                          <span className={getRiskColor(bom.overall_risk_level)}>
                            {bom.overall_risk_level.toUpperCase()}
                          </span>
                        </div>
          </div>
        </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-sm text-slate-400">
                          Created {new Date(bom.created_at).toLocaleDateString()}
                        </div>
                        <div className="text-sm">
                          <span className="text-slate-400">Compliance: </span>
                          <span className={`font-medium ${bom.compliance_score > 80 ? 'text-green-400' : bom.compliance_score > 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {bom.compliance_score}%
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button variant="ghost" size="sm" icon={Eye}>
                          View
                        </Button>
                        <Button variant="ghost" size="sm" icon={Download}>
                          Export
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <FileText className="h-8 w-8 text-slate-400" />
                </div>
                <p className="text-slate-300 font-medium mb-2">No BOM documents yet</p>
                <p className="text-slate-500 text-sm mb-4">Create your first AI Bill of Materials to document system components</p>
                <Button 
                  icon={Plus}
                  onClick={() => setActiveTab('create')}
                >
                  Create BOM
                </Button>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Create BOM Tab */}
      {activeTab === 'create' && (
        <Card title="Create New BOM" icon={<PlusCircle className="h-5 w-5 text-green-400" />}>
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  BOM Name
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Credit Risk Model BOM"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Model Name
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Credit Risk Model v2.1"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description
              </label>
              <textarea
                rows={3}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe the AI system and its components..."
              />
            </div>

            <div className="flex space-x-4">
              <Button>
                Generate BOM
              </Button>
              <Button variant="outline">
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Analyze Tab */}
      {activeTab === 'analyze' && (
        <Card title="BOM Analysis" icon={<Brain className="h-5 w-5 text-purple-400" />}>
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Brain className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-300 font-medium mb-2">BOM Analysis</p>
            <p className="text-slate-500 text-sm">Select a BOM document to analyze its components and dependencies</p>
          </div>
        </Card>
      )}

      {/* Compliance Tab */}
      {activeTab === 'compliance' && (
        <Card title="Compliance Check" icon={<Shield className="h-5 w-5 text-green-400" />}>
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Shield className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-300 font-medium mb-2">Compliance Verification</p>
            <p className="text-slate-500 text-sm">Check BOM compliance against regulatory requirements</p>
          </div>
        </Card>
      )}

      {/* Export Tab */}
      {activeTab === 'export' && (
        <Card title="Export BOM" icon={<Download className="h-5 w-5 text-blue-400" />}>
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Download className="h-8 w-8 text-slate-400" />
                </div>
            <p className="text-slate-300 font-medium mb-2">Export BOM Documents</p>
            <p className="text-slate-500 text-sm">Export BOM data in various formats (JSON, CSV, PDF)</p>
      </div>
        </Card>
      )}
    </PageWrapper>
  )
}
