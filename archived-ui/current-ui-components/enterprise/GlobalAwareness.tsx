import React, { useMemo } from 'react'
import { 
  ChartBarIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  SparklesIcon 
} from '@heroicons/react/24/outline'

interface RealModel {
  id: string
  name: string
  version: string
  type: 'llm' | 'classic_ml'
  framework: string
  status: 'active' | 'inactive' | 'deprecated'
  created_at: string
  updated_at: string
  performance_metrics: {
    accuracy: number
    precision: number
    recall: number
    f1_score: number
  }
  bias_analysis: {
    overall_fairness_score: number
    flagged_attributes: string[]
    risk_level: 'low' | 'medium' | 'high' | 'critical'
  }
}

interface RealIncident {
  id: string
  model_id: string
  model_name: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  type: 'bias_detected' | 'performance_degradation' | 'data_drift' | 'security_issue'
  description: string
  detected_at: string
  status: 'active' | 'acknowledged' | 'mitigated' | 'resolved'
  metrics: {
    metric_name: string
    value: number
    threshold: number
    protected_attribute: string
  }
  impact_assessment: {
    affected_users: number
    business_impact: string
    compliance_risk: string
  }
}

const GlassCard = ({ children, className = "" }: {
  children: React.ReactNode
  className?: string
}) => (
  <div className={`
    bg-white/70 backdrop-blur-xl border border-white/20 rounded-2xl p-6
    shadow-lg hover:shadow-xl transition-all duration-300
    hover:bg-white/80 hover:scale-[1.02]
    ${className}
  `}>
    {children}
  </div>
)

export const GlobalAwareness = ({ models, incidents }: {
  models: RealModel[]
  incidents: RealIncident[]
}) => {
  const activeModels = models.filter(m => m.status === 'active').length
  const criticalIncidents = incidents.filter(i => i.severity === 'critical' && i.status === 'active').length
  const overallHealth = useMemo(() => {
    const totalModels = models.length
    const healthyModels = models.filter(m => m.bias_analysis.risk_level === 'low').length
    return totalModels > 0 ? (healthyModels / totalModels) * 100 : 0
  }, [models])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <GlassCard className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10" />
        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
              <ChartBarIcon className="w-6 h-6 text-white" />
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">{activeModels}</div>
              <div className="text-sm text-gray-600">Active Models</div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${(activeModels / models.length) * 100}%` }}
              />
            </div>
            <span className="text-sm text-gray-600">{models.length} total</span>
          </div>
        </div>
      </GlassCard>

      <GlassCard className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10" />
        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg">
              <CheckCircleIcon className="w-6 h-6 text-white" />
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">{overallHealth.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">System Health</div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${overallHealth}%` }}
              />
            </div>
            <span className="text-sm text-gray-600">Healthy</span>
          </div>
        </div>
      </GlassCard>

      <GlassCard className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-orange-500/10" />
        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg">
              <ExclamationTriangleIcon className="w-6 h-6 text-white" />
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">{criticalIncidents}</div>
              <div className="text-sm text-gray-600">Critical Issues</div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-red-500 to-orange-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${(criticalIncidents / Math.max(incidents.length, 1)) * 100}%` }}
              />
            </div>
            <span className="text-sm text-gray-600">{incidents.length} total</span>
          </div>
        </div>
      </GlassCard>

      <GlassCard className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-indigo-500/10" />
        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {models.filter(m => m.bias_analysis.risk_level === 'low').length}
              </div>
              <div className="text-sm text-gray-600">Fair Models</div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${(models.filter(m => m.bias_analysis.risk_level === 'low').length / models.length) * 100}%` }}
              />
            </div>
            <span className="text-sm text-gray-600">Low Risk</span>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
