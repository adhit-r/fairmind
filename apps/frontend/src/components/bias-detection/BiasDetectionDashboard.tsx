"use client"

import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { 
  ChartBarIcon, 
  ShieldCheckIcon, 
  EyeIcon, 
  CogIcon,
  BellIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UserGroupIcon,
  BeakerIcon,
  DocumentTextIcon,
  ArrowTrendingUpIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  DocumentCheckIcon
} from '@heroicons/react/24/outline'

// Types for Bias Detection
interface BiasMetric {
  name: string
  value: number
  threshold: number
  status: 'pass' | 'warning' | 'fail'
  trend: 'improving' | 'stable' | 'worsening'
  description: string
}

interface ProtectedAttribute {
  name: string
  values: string[]
  distribution: Record<string, number>
  metrics: BiasMetric[]
}

interface BiasIncident {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  model: string
  attribute: string
  metric: string
  value: number
  threshold: number
  timestamp: string
  status: 'active' | 'acknowledged' | 'mitigated' | 'resolved'
  description: string
}

interface MitigationAction {
  id: string
  incidentId: string
  action: string
  description: string
  timestamp: string
  user: string
  status: 'pending' | 'in_progress' | 'completed'
  beforeMetrics: Record<string, number>
  afterMetrics?: Record<string, number>
}

// Bias Heatmap Component
const BiasHeatmap = ({ data }: { data: Record<string, Record<string, BiasMetric>> }) => {
  const attributes = Object.keys(data)
  const metrics = Object.keys(data[attributes[0]] || {})

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass': return 'bg-green-100 text-green-800 border-green-200'
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'fail': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Bias Heatmap</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="text-left p-2 font-medium text-gray-700">Attribute</th>
              {metrics.map(metric => (
                <th key={metric} className="text-center p-2 font-medium text-gray-700">{metric}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {attributes.map(attr => (
              <tr key={attr} className="border-t border-gray-100">
                <td className="p-2 font-medium text-gray-900">{attr}</td>
                {metrics.map(metric => {
                  const biasMetric = data[attr]?.[metric]
                  return (
                    <td key={metric} className="p-2 text-center">
                      {biasMetric ? (
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(biasMetric.status)}`}>
                          {biasMetric.value.toFixed(2)}
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Executive Overview Component
const ExecutiveOverview = ({ metrics, incidents }: { 
  metrics: BiasMetric[]
  incidents: BiasIncident[]
}) => {
  const overallAccuracy = 94.2
  const fairnessGap = Math.max(...metrics.map(m => m.value))
  const flaggedSlices = incidents.filter(i => i.status === 'active').length

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="p-2 bg-blue-100 rounded-lg">
            <ChartBarIcon className="w-6 h-6 text-blue-600" />
          </div>
          <span className="text-sm text-gray-500">Overall</span>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{overallAccuracy}%</h3>
        <p className="text-sm text-gray-600">Model Accuracy</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="p-2 bg-red-100 rounded-lg">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
          </div>
          <span className="text-sm text-gray-500">Largest Gap</span>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{fairnessGap.toFixed(1)}%</h3>
        <p className="text-sm text-gray-600">Fairness Gap</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="p-2 bg-yellow-100 rounded-lg">
            <BellIcon className="w-6 h-6 text-yellow-600" />
          </div>
          <span className="text-sm text-gray-500">Active</span>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{flaggedSlices}</h3>
        <p className="text-sm text-gray-600">Flagged Slices</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="p-2 bg-green-100 rounded-lg">
            <ClockIcon className="w-6 h-6 text-green-600" />
          </div>
          <span className="text-sm text-gray-500">Updated</span>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">2m</h3>
        <p className="text-sm text-gray-600">Ago</p>
      </div>
    </div>
  )
}

// Attribute Drill-Down Component
const AttributeDrillDown = ({ attribute, onAttributeChange }: {
  attribute: string
  onAttributeChange: (attr: string) => void
}) => {
  const attributes = ['Gender', 'Race', 'Age', 'Location', 'Intersectional']
  
  const mockData = {
    Gender: {
      distribution: { 'Male': 45, 'Female': 55 },
      metrics: [
        { name: 'Demographic Parity', value: 2.3, threshold: 5, status: 'pass' as const, trend: 'stable' as const },
        { name: 'Equalized Odds', value: 3.1, threshold: 5, status: 'pass' as const, trend: 'improving' as const },
        { name: 'Calibration', value: 1.8, threshold: 3, status: 'pass' as const, trend: 'stable' as const }
      ]
    }
  }

  const data = mockData[attribute as keyof typeof mockData]

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Attribute Analysis</h3>
        <select 
          value={attribute} 
          onChange={(e) => onAttributeChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {attributes.map(attr => (
            <option key={attr} value={attr}>{attr}</option>
          ))}
        </select>
      </div>

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Distribution Chart */}
          <div>
            <h4 className="font-medium text-gray-900 mb-4">Data Distribution</h4>
            <div className="space-y-3">
              {Object.entries(data.distribution).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{key}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${value}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900">{value}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Metrics Chart */}
          <div>
            <h4 className="font-medium text-gray-900 mb-4">Fairness Metrics</h4>
            <div className="space-y-4">
              {data.metrics.map(metric => (
                <div key={metric.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{metric.name}</p>
                    <p className="text-xs text-gray-500">Threshold: {metric.threshold}%</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-bold ${
                      metric.status === 'pass' ? 'text-green-600' :
                      metric.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {metric.value.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500">{metric.trend}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// LLM Bias View Component
const LLMBiasView = () => {
  const [selectedPrompt, setSelectedPrompt] = useState('')
  const [weatScores, setWeatScores] = useState({
    gender: 0.15,
    race: 0.22,
    occupation: 0.08,
    sentiment: 0.12
  })

  const promptTemplates = [
    "The doctor said...",
    "The nurse said...",
    "The CEO said...",
    "The assistant said..."
  ]

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">LLM Bias Analysis</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* WEAT/SEAT Scores */}
        <div>
          <h4 className="font-medium text-gray-900 mb-4">Embedding Bias Scores</h4>
          <div className="space-y-4">
            {Object.entries(weatScores).map(([dimension, score]) => (
              <div key={dimension} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-900 capitalize">{dimension}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${score > 0.2 ? 'bg-red-500' : score > 0.1 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(score * 500, 100)}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900">{score.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Prompt Testing Sandbox */}
        <div>
          <h4 className="font-medium text-gray-900 mb-4">Prompt Testing</h4>
          <div className="space-y-4">
            <select 
              value={selectedPrompt}
              onChange={(e) => setSelectedPrompt(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a prompt template</option>
              {promptTemplates.map(prompt => (
                <option key={prompt} value={prompt}>{prompt}</option>
              ))}
            </select>
            
            {selectedPrompt && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Minimal Pair Analysis:</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>"{selectedPrompt} he..."</span>
                    <span className="text-green-600">Toxicity: 0.02</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>"{selectedPrompt} she..."</span>
                    <span className="text-red-600">Toxicity: 0.08</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Alerts & Incidents Component
const AlertsIncidents = ({ incidents }: { incidents: BiasIncident[] }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Active Alerts & Incidents</h3>
      
      <div className="space-y-4">
        {incidents.filter(i => i.status === 'active').map(incident => (
          <div key={incident.id} className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(incident.severity)}`}>
                  {incident.severity.toUpperCase()}
                </span>
                <span className="text-sm font-medium text-gray-900">{incident.model}</span>
              </div>
              <span className="text-xs text-gray-500">{incident.timestamp}</span>
            </div>
            
            <p className="text-sm text-gray-600 mb-2">{incident.description}</p>
            
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{incident.attribute} • {incident.metric}</span>
              <span>Value: {incident.value.toFixed(2)}% (Threshold: {incident.threshold}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Mitigation & Audit Component
const MitigationAudit = ({ incidents, mitigations }: { 
  incidents: BiasIncident[]
  mitigations: MitigationAction[]
}) => {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Mitigation & Audit Trail</h3>
      
      <div className="space-y-6">
        {/* Action Center */}
        <div>
          <h4 className="font-medium text-gray-900 mb-4">Recommended Actions</h4>
          <div className="space-y-3">
            {incidents.filter(i => i.status === 'active').map(incident => (
              <div key={incident.id} className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900">{incident.model}</span>
                  <span className="text-xs text-gray-500">{incident.attribute}</span>
                </div>
                <p className="text-sm text-gray-600 mb-3">{incident.description}</p>
                <div className="flex space-x-2">
                  <button className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">
                    Reweigh Data
                  </button>
                  <button className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700">
                    Adjust Threshold
                  </button>
                  <button className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700">
                    Retrain Model
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Log */}
        <div>
          <h4 className="font-medium text-gray-900 mb-4">Audit Log</h4>
          <div className="space-y-3">
            {mitigations.map(mitigation => (
              <div key={mitigation.id} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900">{mitigation.action}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    mitigation.status === 'completed' ? 'bg-green-100 text-green-800' :
                    mitigation.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {mitigation.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{mitigation.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>By: {mitigation.user}</span>
                  <span>{mitigation.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BiasDetectionDashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedAttribute, setSelectedAttribute] = useState('Gender')

  // Mock data
  const biasMetrics: BiasMetric[] = [
    { name: 'Demographic Parity', value: 2.3, threshold: 5, status: 'pass', trend: 'stable', description: 'Difference in positive prediction rates' },
    { name: 'Equalized Odds', value: 3.1, threshold: 5, status: 'pass', trend: 'improving', description: 'Difference in TPR and FPR' },
    { name: 'Calibration', value: 1.8, threshold: 3, status: 'pass', trend: 'stable', description: 'Prediction confidence calibration' },
    { name: 'Statistical Parity', value: 4.2, threshold: 5, status: 'pass', trend: 'worsening', description: 'Overall fairness measure' }
  ]

  const incidents: BiasIncident[] = [
    {
      id: '1',
      severity: 'high',
      model: 'Credit Risk Model v2.1',
      attribute: 'Race',
      metric: 'Demographic Parity',
      value: 7.2,
      threshold: 5,
      timestamp: '2024-01-15 14:30',
      status: 'active',
      description: 'Model shows 7.2% bias in loan approval rates by race'
    },
    {
      id: '2',
      severity: 'medium',
      model: 'Fraud Detection Model',
      attribute: 'Age',
      metric: 'Equalized Odds',
      value: 4.8,
      threshold: 5,
      timestamp: '2024-01-15 13:45',
      status: 'acknowledged',
      description: 'False positive rate differs by age group'
    }
  ]

  const mitigations: MitigationAction[] = [
    {
      id: '1',
      incidentId: '1',
      action: 'Data Reweighting',
      description: 'Applied demographic parity constraints to training data',
      timestamp: '2024-01-15 15:00',
      user: 'Dr. Sarah Chen',
      status: 'completed',
      beforeMetrics: { 'Demographic Parity': 7.2 },
      afterMetrics: { 'Demographic Parity': 3.1 }
    }
  ]

  const heatmapData: Record<string, Record<string, BiasMetric>> = {
    'Gender': {
      'Demographic Parity': { name: 'Demographic Parity', value: 2.3, threshold: 5, status: 'pass' as const, trend: 'stable' as const, description: '' },
      'Equalized Odds': { name: 'Equalized Odds', value: 3.1, threshold: 5, status: 'pass' as const, trend: 'improving' as const, description: '' },
      'Calibration': { name: 'Calibration', value: 1.8, threshold: 3, status: 'pass' as const, trend: 'stable' as const, description: '' }
    },
    'Race': {
      'Demographic Parity': { name: 'Demographic Parity', value: 7.2, threshold: 5, status: 'fail' as const, trend: 'worsening' as const, description: '' },
      'Equalized Odds': { name: 'Equalized Odds', value: 4.8, threshold: 5, status: 'pass' as const, trend: 'stable' as const, description: '' },
      'Calibration': { name: 'Calibration', value: 2.1, threshold: 3, status: 'pass' as const, trend: 'stable' as const, description: '' }
    }
  }

  const tabs = [
    { id: 'overview', name: 'Executive Overview', icon: ChartBarIcon },
    { id: 'drilldown', name: 'Attribute Analysis', icon: MagnifyingGlassIcon },
    { id: 'llm', name: 'LLM Bias', icon: BeakerIcon },
    { id: 'alerts', name: 'Alerts & Incidents', icon: BellIcon },
    { id: 'mitigation', name: 'Mitigation & Audit', icon: DocumentCheckIcon }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Bias Detection Dashboard</h1>
              <p className="text-sm text-gray-600">Multi-layer bias detection and mitigation system</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 rounded-full">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-green-700">Monitoring Active</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-8">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            <ExecutiveOverview metrics={biasMetrics} incidents={incidents} />
            <BiasHeatmap data={heatmapData} />
          </div>
        )}

        {activeTab === 'drilldown' && (
          <AttributeDrillDown 
            attribute={selectedAttribute} 
            onAttributeChange={setSelectedAttribute} 
          />
        )}

        {activeTab === 'llm' && (
          <LLMBiasView />
        )}

        {activeTab === 'alerts' && (
          <AlertsIncidents incidents={incidents} />
        )}

        {activeTab === 'mitigation' && (
          <MitigationAudit incidents={incidents} mitigations={mitigations} />
        )}
      </main>
    </div>
  )
}

