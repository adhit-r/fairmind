'use client'

import React, { useState, useEffect } from 'react'

interface ModelProvenance {
  id: string
  name: string
  version: string
  modelType: 'classification' | 'regression' | 'nlp' | 'computer-vision' | 'recommendation'
  status: 'active' | 'deprecated' | 'testing' | 'archived'
  createdAt: string
  lastUpdated: string
  creator: string
  description: string
  lineage: LineageNode[]
  dataSources: DataSource[]
  trainingHistory: TrainingRun[]
  performanceMetrics: PerformanceMetric[]
  complianceStatus: 'compliant' | 'non-compliant' | 'review' | 'pending'
}

interface LineageNode {
  id: string
  type: 'model' | 'dataset' | 'preprocessing' | 'training' | 'evaluation'
  name: string
  version: string
  timestamp: string
  description: string
  parentIds: string[]
  metadata: Record<string, any>
}

interface DataSource {
  id: string
  name: string
  type: 'training' | 'validation' | 'test' | 'external'
  source: string
  version: string
  size: number
  records: number
  lastUpdated: string
  license: string
  description: string
  qualityScore: number
}

interface TrainingRun {
  id: string
  timestamp: string
  duration: number
  hyperparameters: Record<string, any>
  metrics: Record<string, number>
  status: 'completed' | 'failed' | 'running' | 'cancelled'
  artifacts: string[]
  logs: string
}

interface PerformanceMetric {
  name: string
  value: number
  unit: string
  timestamp: string
  environment: string
  threshold: number
  status: 'pass' | 'fail' | 'warning'
}

interface ProvenanceMetrics {
  totalModels: number
  activeModels: number
  averageLineageDepth: number
  dataQualityScore: number
  complianceRate: number
  lastAudit: string
  nextReview: string
}

export default function Provenance() {
  const [loading, setLoading] = useState(true)
  const [models, setModels] = useState<ModelProvenance[]>([])
  const [metrics, setMetrics] = useState<ProvenanceMetrics>({
    totalModels: 0,
    activeModels: 0,
    averageLineageDepth: 0,
    dataQualityScore: 0,
    complianceRate: 0,
    lastAudit: '',
    nextReview: ''
  })
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  useEffect(() => {
    const timer = setTimeout(() => {
      const mockModels: ModelProvenance[] = [
        {
          id: '1',
          name: 'Credit Risk Classifier',
          version: '2.1.0',
          modelType: 'classification',
          status: 'active',
          createdAt: '2024-01-10',
          lastUpdated: '2024-01-20',
          creator: 'ML Team',
          description: 'Binary classification model for credit risk assessment',
          complianceStatus: 'compliant',
          lineage: [
            {
              id: 'l1',
              type: 'dataset',
              name: 'Credit Dataset v1.2',
              version: '1.2.0',
              timestamp: '2024-01-08',
              description: 'Initial data collection and preprocessing',
              parentIds: [],
              metadata: { records: 50000, features: 25 }
            },
            {
              id: 'l2',
              type: 'preprocessing',
              name: 'Feature Engineering Pipeline',
              version: '1.0.0',
              timestamp: '2024-01-09',
              description: 'Feature extraction and normalization',
              parentIds: ['l1'],
              metadata: { features_created: 15, features_selected: 20 }
            },
            {
              id: 'l3',
              type: 'training',
              name: 'Model Training v2.1',
              version: '2.1.0',
              timestamp: '2024-01-15',
              description: 'XGBoost model training with hyperparameter tuning',
              parentIds: ['l2'],
              metadata: { algorithm: 'XGBoost', accuracy: 0.89 }
            }
          ],
          dataSources: [
            {
              id: 'ds1',
              name: 'Customer Credit Data',
              type: 'training',
              source: 'Internal Database',
              version: '1.2.0',
              size: 2500000,
              records: 50000,
              lastUpdated: '2024-01-08',
              license: 'Internal Use Only',
              description: 'Historical customer credit data with risk labels',
              qualityScore: 92
            }
          ],
          trainingHistory: [
            {
              id: 'tr1',
              timestamp: '2024-01-15 14:30:00',
              duration: 3600,
              hyperparameters: {
                learning_rate: 0.1,
                max_depth: 6,
                n_estimators: 100
              },
              metrics: {
                accuracy: 0.89,
                precision: 0.87,
                recall: 0.91,
                f1_score: 0.89
              },
              status: 'completed',
              artifacts: ['model.pkl', 'feature_importance.json', 'training_logs.txt'],
              logs: 'Training completed successfully with 89% accuracy'
            }
          ],
          performanceMetrics: [
            {
              name: 'Accuracy',
              value: 0.89,
              unit: '%',
              timestamp: '2024-01-20 10:00:00',
              environment: 'Production',
              threshold: 0.85,
              status: 'pass'
            },
            {
              name: 'Latency',
              value: 45,
              unit: 'ms',
              timestamp: '2024-01-20 10:00:00',
              environment: 'Production',
              threshold: 100,
              status: 'pass'
            }
          ]
        },
        {
          id: '2',
          name: 'Fraud Detection Model',
          version: '1.5.2',
          modelType: 'classification',
          status: 'active',
          createdAt: '2024-01-05',
          lastUpdated: '2024-01-18',
          creator: 'Security Team',
          description: 'Real-time fraud detection using deep learning',
          complianceStatus: 'review',
          lineage: [
            {
              id: 'l4',
              type: 'dataset',
              name: 'Transaction Dataset',
              version: '2.0.0',
              timestamp: '2024-01-03',
              description: 'Transaction data with fraud labels',
              parentIds: [],
              metadata: { records: 100000, features: 30 }
            },
            {
              id: 'l5',
              type: 'training',
              name: 'Neural Network Training',
              version: '1.5.2',
              timestamp: '2024-01-10',
              description: 'Deep learning model training',
              parentIds: ['l4'],
              metadata: { architecture: 'CNN', accuracy: 0.94 }
            }
          ],
          dataSources: [
            {
              id: 'ds2',
              name: 'Transaction Data',
              type: 'training',
              source: 'Payment Gateway',
              version: '2.0.0',
              size: 5000000,
              records: 100000,
              lastUpdated: '2024-01-03',
              license: 'Commercial',
              description: 'Real-time transaction data with fraud indicators',
              qualityScore: 88
            }
          ],
          trainingHistory: [
            {
              id: 'tr2',
              timestamp: '2024-01-10 09:00:00',
              duration: 7200,
              hyperparameters: {
                epochs: 100,
                batch_size: 32,
                learning_rate: 0.001
              },
              metrics: {
                accuracy: 0.94,
                precision: 0.92,
                recall: 0.95,
                f1_score: 0.93
              },
              status: 'completed',
              artifacts: ['model.h5', 'training_history.json'],
              logs: 'Neural network training completed with 94% accuracy'
            }
          ],
          performanceMetrics: [
            {
              name: 'Accuracy',
              value: 0.94,
              unit: '%',
              timestamp: '2024-01-18 15:30:00',
              environment: 'Production',
              threshold: 0.90,
              status: 'pass'
            }
          ]
        }
      ]

      setModels(mockModels)
      
      const activeModels = mockModels.filter(m => m.status === 'active').length
      const avgLineageDepth = Math.round(mockModels.reduce((sum, m) => sum + m.lineage.length, 0) / mockModels.length)
      const avgDataQuality = Math.round(mockModels.reduce((sum, m) => 
        sum + m.dataSources.reduce((dsSum, ds) => dsSum + ds.qualityScore, 0) / m.dataSources.length, 0) / mockModels.length)
      const complianceRate = Math.round((mockModels.filter(m => m.complianceStatus === 'compliant').length / mockModels.length) * 100)

      setMetrics({
        totalModels: mockModels.length,
        activeModels: activeModels,
        averageLineageDepth: avgLineageDepth,
        dataQualityScore: avgDataQuality,
        complianceRate: complianceRate,
        lastAudit: '2024-01-20 16:00:00',
        nextReview: '2024-02-20'
      })
      
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  const filteredModels = models.filter(model => {
    const typeMatch = selectedType === 'all' || model.modelType === selectedType
    const statusMatch = selectedStatus === 'all' || model.status === selectedStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20'
      case 'deprecated': return 'text-gray-400 bg-gray-500/20'
      case 'testing': return 'text-yellow-400 bg-yellow-500/20'
      case 'archived': return 'text-blue-400 bg-blue-500/20'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'text-green-400'
      case 'non-compliant': return 'text-red-400'
      case 'review': return 'text-yellow-400'
      case 'pending': return 'text-blue-400'
      default: return 'text-muted-foreground'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'classification': return '🎯'
      case 'regression': return '📈'
      case 'nlp': return '💬'
      case 'computer-vision': return '👁️'
      case 'recommendation': return '💡'
      default: return '🤖'
    }
  }

  const getLineageTypeIcon = (type: string) => {
    switch (type) {
      case 'model': return '🤖'
      case 'dataset': return '📊'
      case 'preprocessing': return '🔧'
      case 'training': return '🎓'
      case 'evaluation': return '📋'
      default: return '📦'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
        <div className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
            Model Provenance
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground font-mono">
            Model Lineage & Audit Trail Tracking
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground font-mono">Loading Model Provenance...</p>
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
          Model Provenance
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          Model Lineage & Audit Trail Tracking
        </p>
      </div>

      {/* Provenance Overview */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-foreground">Provenance Overview</h2>
            <p className="text-sm text-muted-foreground font-mono">
              Model lineage tracking and audit trail management
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gold">{metrics.complianceRate}%</div>
            <span className="text-sm text-muted-foreground font-mono">Compliance Rate</span>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.totalModels}</div>
            <div className="text-xs text-muted-foreground font-mono">Total Models</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.activeModels}</div>
            <div className="text-xs text-muted-foreground font-mono">Active Models</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.averageLineageDepth}</div>
            <div className="text-xs text-muted-foreground font-mono">Avg Lineage Depth</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-foreground">{metrics.dataQualityScore}%</div>
            <div className="text-xs text-muted-foreground font-mono">Data Quality Score</div>
          </div>
        </div>
      </div>

      {/* Audit Status */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Last Audit</h3>
          <div className="text-sm font-bold text-foreground">{metrics.lastAudit}</div>
          <p className="text-xs text-muted-foreground font-mono">Comprehensive provenance audit</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-bold text-foreground mb-2">Next Review</h3>
          <div className="text-sm font-bold text-foreground">{metrics.nextReview}</div>
          <p className="text-xs text-muted-foreground font-mono">Scheduled lineage review</p>
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
            <option value="classification">Classification</option>
            <option value="regression">Regression</option>
            <option value="nlp">NLP</option>
            <option value="computer-vision">Computer Vision</option>
            <option value="recommendation">Recommendation</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1 text-sm bg-card border border-border rounded-md font-mono"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="deprecated">Deprecated</option>
            <option value="testing">Testing</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <button className="px-4 py-2 bg-gold text-gold-foreground rounded-md font-mono text-sm hover:bg-gold/90 transition-colors">
          Generate Lineage Report
        </button>
      </div>

      {/* Model Provenance */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-foreground">Model Provenance</h2>
        
        <div className="grid gap-4">
          {filteredModels.map((model) => (
            <div key={model.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{getTypeIcon(model.modelType)}</span>
                    <h3 className="text-lg font-bold text-foreground">{model.name}</h3>
                    <span className="text-sm font-mono text-muted-foreground">v{model.version}</span>
                    <span className={`inline-flex px-2 py-1 rounded text-xs font-mono ${getStatusColor(model.status)}`}>
                      {model.status.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${getComplianceColor(model.complianceStatus)}`}>
                      {model.complianceStatus.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono mb-3">{model.description}</p>
                  
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Creator</span>
                      <div className="text-sm font-bold text-foreground">{model.creator}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Created</span>
                      <div className="text-sm font-bold text-foreground">{model.createdAt}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Last Updated</span>
                      <div className="text-sm font-bold text-foreground">{model.lastUpdated}</div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground font-mono">Lineage Depth</span>
                      <div className="text-sm font-bold text-foreground">{model.lineage.length}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Lineage Graph */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Lineage Graph</h4>
                <div className="space-y-2">
                  {model.lineage.map((node, index) => (
                    <div key={node.id} className="flex items-center gap-3 p-3 border border-border rounded-lg">
                      <span className="text-xl">{getLineageTypeIcon(node.type)}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h5 className="text-sm font-bold text-foreground">{node.name}</h5>
                          <span className="text-xs font-mono text-muted-foreground">v{node.version}</span>
                          <span className="text-xs font-mono text-muted-foreground">{node.type}</span>
                        </div>
                        <p className="text-xs text-muted-foreground font-mono">{node.description}</p>
                        <div className="text-xs text-muted-foreground font-mono mt-1">
                          {node.timestamp} | Parents: {node.parentIds.length}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Data Sources */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Data Sources</h4>
                <div className="grid gap-3 sm:grid-cols-2">
                  {model.dataSources.map((source) => (
                    <div key={source.id} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-bold text-foreground">{source.name}</h5>
                        <span className="text-xs font-mono text-muted-foreground">{source.type}</span>
                      </div>
                      <p className="text-xs text-muted-foreground font-mono mb-2">{source.description}</p>
                      <div className="grid gap-2 text-xs text-muted-foreground font-mono">
                        <div>Source: {source.source} v{source.version}</div>
                        <div>Records: {source.records.toLocaleString()} | Size: {(source.size / 1000000).toFixed(1)}MB</div>
                        <div>Quality Score: {source.qualityScore}% | License: {source.license}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-bold text-foreground">Performance Metrics</h4>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {model.performanceMetrics.map((metric, index) => (
                    <div key={index} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-bold text-foreground">{metric.name}</h5>
                        <span className={`text-xs font-mono ${
                          metric.status === 'pass' ? 'text-green-400' : 
                          metric.status === 'fail' ? 'text-red-400' : 
                          'text-yellow-400'
                        }`}>
                          {metric.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-lg font-bold text-foreground">{metric.value}{metric.unit}</div>
                      <div className="text-xs text-muted-foreground font-mono">
                        Threshold: {metric.threshold}{metric.unit} | {metric.environment}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                  <span>Type: {model.modelType}</span>
                  <span>Status: {model.status}</span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    View Lineage
                  </button>
                  <button className="px-3 py-1 text-xs bg-card border border-border rounded font-mono hover:bg-accent transition-colors">
                    Export Provenance
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
