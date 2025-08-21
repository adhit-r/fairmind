"use client"

import { useState, useEffect } from 'react'
import { 
  Brain, 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Download,
  Upload,
  Search,
  Filter,
  Eye,
  Shield,
  Activity,
  TrendingUp,
  BarChart3,
  Database,
  Cpu,
  Zap,
  Target,
  Users,
  Globe,
  Lock,
  RefreshCw,
  Plus,
  Settings,
  Info,
  HelpCircle,
  Star,
  Award,
  Calendar,
  MapPin,
  UserCheck,
  Scale,
  ChevronRight,
  ChevronDown,
  Sparkles,
  BarChart,
  PieChart,
  LineChart,
  ArrowRight,
  FileUp,
  TestTube,
  Play,
  Pause,
  Stop,
  RotateCcw,
  Save,
  Edit,
  Trash2,
  Copy,
  Share,
  Bookmark,
  Tag,
  Hash,
  Link,
  Unlink,
  X,
  GitBranch,
  GitCommit,
  GitMerge,
  GitPullRequest,
  GitCompare,
  GitFork
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface ModelDNA {
  id: string
  name: string
  version: string
  type: string
  framework: string
  architecture: string
  parameters: number
  training_data: string
  training_metrics: {
    accuracy: number
    precision: number
    recall: number
    f1_score: number
  }
  bias_metrics: {
    demographic_parity: number
    equalized_odds: number
    individual_fairness: number
  }
  provenance: {
    created_by: string
    created_date: string
    last_modified: string
    git_commit: string
    dataset_version: string
  }
  compliance: {
    gdpr_compliant: boolean
    hipaa_compliant: boolean
    sox_compliant: boolean
    nist_compliant: boolean
  }
  security: {
    vulnerability_scan: string
    adversarial_robustness: number
    data_privacy_score: number
  }
  documentation: {
    model_card: string
    data_sheet: string
    technical_specs: string
  }
}

export default function ModelDNAPage() {
  const [models, setModels] = useState<ModelDNA[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<ModelDNA | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    loadModelDNA()
  }, [])

  const loadModelDNA = async () => {
    try {
      setLoading(true)
      
      // In a real implementation, this would come from the API
      // For now, we'll generate realistic model DNA data
      const datasets = await fairmindAPI.getAvailableDatasets()
      
      const mockModels: ModelDNA[] = datasets.map((dataset, index) => ({
        id: `model-${index + 1}`,
        name: `${dataset.name} Model`,
        version: `v${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
        type: ['classification', 'regression', 'clustering'][Math.floor(Math.random() * 3)],
        framework: ['TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost'][Math.floor(Math.random() * 4)],
        architecture: ['Neural Network', 'Random Forest', 'Gradient Boosting', 'Linear Model'][Math.floor(Math.random() * 4)],
        parameters: Math.floor(Math.random() * 1000000) + 1000,
        training_data: `${dataset.name} Dataset`,
        training_metrics: {
          accuracy: Math.random() * 0.2 + 0.8,
          precision: Math.random() * 0.2 + 0.8,
          recall: Math.random() * 0.2 + 0.8,
          f1_score: Math.random() * 0.2 + 0.8
        },
        bias_metrics: {
          demographic_parity: Math.random() * 0.3 + 0.7,
          equalized_odds: Math.random() * 0.3 + 0.7,
          individual_fairness: Math.random() * 0.3 + 0.7
        },
        provenance: {
          created_by: 'AI Team',
          created_date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
          last_modified: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
          git_commit: `commit_${Math.random().toString(36).substr(2, 8)}`,
          dataset_version: `v${Math.floor(Math.random() * 3) + 1}.${Math.floor(Math.random() * 10)}`
        },
        compliance: {
          gdpr_compliant: Math.random() > 0.3,
          hipaa_compliant: Math.random() > 0.4,
          sox_compliant: Math.random() > 0.5,
          nist_compliant: Math.random() > 0.2
        },
        security: {
          vulnerability_scan: Math.random() > 0.2 ? 'Passed' : 'Failed',
          adversarial_robustness: Math.random() * 0.4 + 0.6,
          data_privacy_score: Math.random() * 0.4 + 0.6
        },
        documentation: {
          model_card: 'Available',
          data_sheet: 'Available',
          technical_specs: 'Available'
        }
      }))
      
      setModels(mockModels)
    } catch (error) {
      console.error('Error loading model DNA:', error)
      setModels([])
    } finally {
      setLoading(false)
    }
  }

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.framework.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || model.type === filterType
    return matchesSearch && matchesFilter
  })

  const getComplianceScore = (model: ModelDNA) => {
    const complianceChecks = Object.values(model.compliance)
    return (complianceChecks.filter(Boolean).length / complianceChecks.length) * 100
  }

  const getBiasScore = (model: ModelDNA) => {
    const biasMetrics = Object.values(model.bias_metrics)
    return (biasMetrics.reduce((sum, val) => sum + val, 0) / biasMetrics.length) * 100
  }

  const getSecurityScore = (model: ModelDNA) => {
    return (model.security.adversarial_robustness + model.security.data_privacy_score) * 50
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <Brain className="h-8 w-8 mr-3 text-blue-600" />
              Model DNA Registry
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Complete model lineage, provenance, and governance tracking.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <Database className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">{models.length} Models</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <Shield className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">Compliance Ready</span>
              </div>
              <button 
                onClick={loadModelDNA}
                disabled={loading}
                className="flex items-center space-x-2 bg-white border-2 border-black px-3 py-1 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 text-gray-700 ${loading ? 'animate-spin' : ''}`} />
                <span className="text-sm font-bold text-gray-700">Refresh</span>
              </button>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <GitBranch className="h-10 w-10 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search models by name, type, or framework..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Types</option>
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
              <option value="clustering">Clustering</option>
            </select>
            <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Plus className="h-4 w-4 mr-2" />
              Add Model
            </button>
          </div>
        </div>
      </div>

      {/* Models Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-4"></div>
              <div className="h-3 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : filteredModels.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model) => (
            <div
              key={model.id}
              onClick={() => setSelectedModel(model)}
              className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black cursor-pointer hover:shadow-6px-6px-0px-black transition-all duration-200"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg border-2 border-black bg-blue-500">
                    <Brain className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-black text-gray-900">{model.name}</h3>
                    <p className="text-sm font-bold text-gray-600">{model.version}</p>
                  </div>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-gray-600">Type</span>
                  <span className="text-sm font-black text-gray-900 capitalize">{model.type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-gray-600">Framework</span>
                  <span className="text-sm font-black text-gray-900">{model.framework}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-gray-600">Parameters</span>
                  <span className="text-sm font-black text-gray-900">{model.parameters.toLocaleString()}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t-2 border-gray-200">
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-center">
                    <div className="text-lg font-black text-green-600">{getComplianceScore(model).toFixed(0)}%</div>
                    <div className="text-xs font-bold text-gray-600">Compliance</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-black text-blue-600">{getBiasScore(model).toFixed(0)}%</div>
                    <div className="text-xs font-bold text-gray-600">Fairness</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-black text-purple-600">{getSecurityScore(model).toFixed(0)}%</div>
                    <div className="text-xs font-bold text-gray-600">Security</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="text-xs font-bold text-gray-500">
                    {new Date(model.provenance.last_modified).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  {model.compliance.gdpr_compliant && <Shield className="h-4 w-4 text-green-600" />}
                  {model.compliance.nist_compliant && <Award className="h-4 w-4 text-blue-600" />}
                  {model.security.vulnerability_scan === 'Passed' && <CheckCircle className="h-4 w-4 text-green-600" />}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Brain className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-black text-gray-900 mb-2">No Models Found</h3>
          <p className="text-gray-600 font-bold">Try adjusting your search criteria or add a new model.</p>
        </div>
      )}

      {/* Model Details Modal */}
      {selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-black text-gray-900 flex items-center">
                <Brain className="h-6 w-6 mr-3 text-blue-600" />
                {selectedModel.name} - Model DNA
              </h2>
              <button
                onClick={() => setSelectedModel(null)}
                className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
              >
                <X className="h-5 w-5 text-gray-700" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Basic Information */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Info className="h-5 w-5 mr-2 text-blue-600" />
                    Basic Information
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Version:</span>
                      <span className="font-black text-gray-900">{selectedModel.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Type:</span>
                      <span className="font-black text-gray-900 capitalize">{selectedModel.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Framework:</span>
                      <span className="font-black text-gray-900">{selectedModel.framework}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Architecture:</span>
                      <span className="font-black text-gray-900">{selectedModel.architecture}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Parameters:</span>
                      <span className="font-black text-gray-900">{selectedModel.parameters.toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Training Metrics */}
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2 text-green-600" />
                    Training Metrics
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Accuracy:</span>
                      <span className="font-black text-gray-900">{(selectedModel.training_metrics.accuracy * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Precision:</span>
                      <span className="font-black text-gray-900">{(selectedModel.training_metrics.precision * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Recall:</span>
                      <span className="font-black text-gray-900">{(selectedModel.training_metrics.recall * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">F1 Score:</span>
                      <span className="font-black text-gray-900">{(selectedModel.training_metrics.f1_score * 100).toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bias Metrics & Compliance */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Scale className="h-5 w-5 mr-2 text-red-600" />
                    Bias Metrics
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Demographic Parity:</span>
                      <span className="font-black text-gray-900">{(selectedModel.bias_metrics.demographic_parity * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Equalized Odds:</span>
                      <span className="font-black text-gray-900">{(selectedModel.bias_metrics.equalized_odds * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-bold text-gray-600">Individual Fairness:</span>
                      <span className="font-black text-gray-900">{(selectedModel.bias_metrics.individual_fairness * 100).toFixed(2)}%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center">
                    <Shield className="h-5 w-5 mr-2 text-purple-600" />
                    Compliance Status
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-gray-600">GDPR:</span>
                      <div className="flex items-center">
                        {selectedModel.compliance.gdpr_compliant ? (
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        ) : (
                          <X className="h-4 w-4 text-red-600 mr-2" />
                        )}
                        <span className={`font-black ${selectedModel.compliance.gdpr_compliant ? 'text-green-600' : 'text-red-600'}`}>
                          {selectedModel.compliance.gdpr_compliant ? 'Compliant' : 'Non-Compliant'}
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-gray-600">HIPAA:</span>
                      <div className="flex items-center">
                        {selectedModel.compliance.hipaa_compliant ? (
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        ) : (
                          <X className="h-4 w-4 text-red-600 mr-2" />
                        )}
                        <span className={`font-black ${selectedModel.compliance.hipaa_compliant ? 'text-green-600' : 'text-red-600'}`}>
                          {selectedModel.compliance.hipaa_compliant ? 'Compliant' : 'Non-Compliant'}
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-gray-600">SOX:</span>
                      <div className="flex items-center">
                        {selectedModel.compliance.sox_compliant ? (
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        ) : (
                          <X className="h-4 w-4 text-red-600 mr-2" />
                        )}
                        <span className={`font-black ${selectedModel.compliance.sox_compliant ? 'text-green-600' : 'text-red-600'}`}>
                          {selectedModel.compliance.sox_compliant ? 'Compliant' : 'Non-Compliant'}
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-gray-600">NIST:</span>
                      <div className="flex items-center">
                        {selectedModel.compliance.nist_compliant ? (
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        ) : (
                          <X className="h-4 w-4 text-red-600 mr-2" />
                        )}
                        <span className={`font-black ${selectedModel.compliance.nist_compliant ? 'text-green-600' : 'text-red-600'}`}>
                          {selectedModel.compliance.nist_compliant ? 'Compliant' : 'Non-Compliant'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex justify-center space-x-4">
              <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Download className="h-4 w-4 mr-2" />
                Download Model Card
              </button>
              <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Eye className="h-4 w-4 mr-2" />
                View Lineage
              </button>
              <button className="bg-purple-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-purple-600 shadow-2px-2px-0px-black transition-all duration-200">
                <GitBranch className="h-4 w-4 mr-2" />
                Track Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
