// API Configuration - Updated for backend integration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.fairmind.xyz'

// API Response Types
interface ApiResponse<T> {
  success?: boolean
  data?: T
  error?: string
  message?: string
}

// Dashboard Types
interface GovernanceMetrics {
  totalModels: number
  activeModels: number
  criticalRisks: number
  llmSafetyScore: number
  nistCompliance: number
}

interface RecentActivity {
  id: string
  type: 'model_upload' | 'bias_analysis' | 'security_test' | 'compliance_check'
  modelName: string
  status: 'completed' | 'running' | 'failed'
  timestamp: string
  description: string
}

// Bias Detection Types
interface BiasAnalysisRequest {
  datasetId?: string
  modelId?: string
  modelType?: 'llm' | 'classic_ml'
  targetColumn?: string
  sensitiveColumns?: string[]
  dataset_name?: string
}

interface BiasAnalysisResult {
  id: string
  modelId: string
  modelName: string
  datasetName: string
  status: 'good' | 'warning' | 'error'
  fairnessScore: number
  biasScore: number
  biasTypes: string[]
  recommendations: string[]
  createdAt: string
  modelType: 'llm' | 'classic_ml'
  metrics?: {
    demographic_parity?: number
    equalized_odds?: number
    equal_opportunity?: number
    statistical_parity?: number
    weat_score?: number
    seat_score?: number
  }
  biasDetails?: {
    bias_types: string[]
    risk_level: 'low' | 'medium' | 'high'
  }
}

// Security Testing Types
interface SecurityTestRequest {
  modelId?: string
  testMode?: 'comprehensive' | 'targeted'
  testCategories?: string[]
  testIds?: string[]
  model_name?: string
}

interface SecurityAnalysisResult {
  id: string
  modelId: string
  modelName: string
  overallScore: number
  securityScore: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  vulnerabilities: number
  testSummary: {
    totalTests: number
    passedTests: number
    failedTests: number
    skippedTests: number
  }
  issueBreakdown: {
    critical: number
    high: number
    medium: number
    low: number
  }
  performanceMetrics: {
    executionTime: number
    memoryUsage: number
    cpuUsage: number
  }
  testResults: Array<{
    testId: string
    testName: string
    status: 'passed' | 'failed' | 'skipped'
    severity: 'critical' | 'high' | 'medium' | 'low'
    description: string
    recommendations: string[]
  }>
  recommendations: string[]
  createdAt: string
}

// Model and Dataset Types
interface Dataset {
  id: string
  name: string
  description: string
  size: number
  columns: string[]
  createdAt: string
}

interface Model {
  id: string
  name: string
  type: 'llm' | 'classic_ml'
  framework: string
  version: string
  status: 'active' | 'inactive' | 'testing' | 'pending'
  createdAt: string
  accuracy?: number
  biasScore?: number
  securityScore?: number
  complianceScore?: number
}

interface SecurityTest {
  id: string
  name: string
  category: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
}

// AI BOM Types
interface BOMItem {
  id: string
  name: string
  type: string
  version: string
  license: string
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  vulnerabilities: string[]
}

interface BOMDocument {
  id: string
  modelId: string
  modelName: string
  items: BOMItem[]
  totalItems: number
  riskItems: number
  createdAt: string
}

// API Client Class
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }

  // Dashboard Methods
  async getGovernanceMetrics(): Promise<ApiResponse<GovernanceMetrics>> {
    return this.request<GovernanceMetrics>('/governance/metrics')
  }

  async getRecentActivity(): Promise<ApiResponse<RecentActivity[]>> {
    return this.request<RecentActivity[]>('/activity/recent')
  }

  async getMetricsSummary(): Promise<ApiResponse<any>> {
    return this.request<any>('/metrics/summary')
  }

  // Bias Detection Methods
  async getBiasDatasets(): Promise<ApiResponse<Dataset[]>> {
    return this.request<Dataset[]>('/datasets')
  }

  async getModels(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/models')
  }

  async analyzeBias(request: BiasAnalysisRequest): Promise<ApiResponse<BiasAnalysisResult>> {
    return this.request<BiasAnalysisResult>('/bias/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async analyzeBiasReal(request: BiasAnalysisRequest): Promise<ApiResponse<BiasAnalysisResult>> {
    return this.request<BiasAnalysisResult>('/bias/analyze-real', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getBiasAnalysisHistory(): Promise<ApiResponse<BiasAnalysisResult[]>> {
    return this.request<BiasAnalysisResult[]>('/bias/analysis')
  }

  // Security Testing Methods
  async runSecurityAnalysis(request: SecurityTestRequest): Promise<ApiResponse<SecurityAnalysisResult>> {
    return this.request<SecurityAnalysisResult>('/owasp/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getSecurityTestHistory(): Promise<ApiResponse<SecurityAnalysisResult[]>> {
    return this.request<SecurityAnalysisResult[]>('/owasp/analysis')
  }

  async getSecurityTests(): Promise<ApiResponse<SecurityTest[]>> {
    return this.request<SecurityTest[]>('/owasp/tests')
  }

  async getOWASPCategories(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/owasp/categories')
  }

  // Model Registry Methods
  async getModelRegistry(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/models')
  }

  async registerModel(model: Partial<Model>): Promise<ApiResponse<Model>> {
    return this.request<Model>('/models/register', {
      method: 'POST',
      body: JSON.stringify(model),
    })
  }

  async uploadModel(formData: FormData): Promise<Response> {
    const url = `${this.baseUrl}/models/upload`
    return fetch(url, {
      method: 'POST',
      body: formData,
    })
  }

  // Dataset Management Methods
  async uploadDataset(file: File): Promise<ApiResponse<Dataset>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.request<Dataset>('/datasets/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    })
  }

  async getAvailableDatasets(): Promise<ApiResponse<Dataset[]>> {
    return this.request<Dataset[]>('/datasets/available')
  }

  // AI BOM Methods
  async scanBOM(request: any): Promise<ApiResponse<BOMDocument>> {
    return this.request<BOMDocument>('/bom/scan', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getBOMList(): Promise<ApiResponse<BOMDocument[]>> {
    return this.request<BOMDocument[]>('/bom/list')
  }

  async getBOMById(bomId: string): Promise<ApiResponse<BOMDocument>> {
    return this.request<BOMDocument>(`/bom/${bomId}`)
  }

  async generateComprehensiveBOM(request: any): Promise<ApiResponse<BOMDocument>> {
    return this.request<BOMDocument>('/bom/generate-comprehensive', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // Monitoring Methods
  async getMonitoringMetrics(): Promise<ApiResponse<any>> {
    return this.request<any>('/monitor/drift')
  }

  async getDriftAnalysis(): Promise<ApiResponse<any>> {
    return this.request<any>('/monitor/drift')
  }

  // Compliance Methods
  async getNISTComplianceScore(request: any): Promise<ApiResponse<any>> {
    return this.request<any>('/compliance/nist-score', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // Provenance Methods
  async getProvenanceModels(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/provenance/models')
  }

  async getProvenanceModelCard(modelId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/provenance/model-card/${modelId}`)
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request<{ status: string; timestamp: string }>('/health')
  }
}

// Export singleton instance
export const api = new ApiClient(API_BASE_URL)

// Export types for use in components
export type {
  ApiResponse,
  GovernanceMetrics,
  RecentActivity,
  BiasAnalysisRequest,
  BiasAnalysisResult,
  SecurityTestRequest,
  SecurityAnalysisResult,
  Dataset,
  Model,
  SecurityTest,
  BOMItem,
  BOMDocument,
}
