// Fairmind API Client
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Dataset {
  name: string
  samples: number
  columns: string[]
  description: string
}

export interface BiasAnalysisRequest {
  dataset_name: string
  target_column: string
  sensitive_columns: string[]
  custom_rules?: any[]
  llm_enabled?: boolean
  llm_prompt?: string
  simulation_enabled?: boolean
}

export interface BiasAnalysisResult {
  dataset_name: string
  total_samples: number
  overall_score: number
  assessment_status: string
  issues_found: Array<{
    type: string
    severity: string
    description: string
    details: any
  }>
  bias_details: Record<string, any>
  recommendations: string[]
  custom_rules_results: any[]
  llm_analysis?: any
  simulation_results?: any
}

export interface ModelProvenanceRequest {
  model_name: string
  model_type: string
  dataset_name: string
  training_parameters: Record<string, any>
  performance_metrics: Record<string, any>
}

export interface ProvenanceResult {
  model_id: string
  signature: string
  timestamp: string
  lineage: any
  audit_trail: any[]
}

export interface SecurityScanRequest {
  model_id: string
  scan_type: 'owasp' | 'comprehensive'
  parameters?: Record<string, any>
}

export interface SecurityScanResult {
  scan_id: string
  vulnerabilities: any[]
  risk_score: number
  recommendations: string[]
  compliance_status: Record<string, boolean>
}

class FairmindAPI {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }

    const response = await fetch(url, { ...defaultOptions, ...options })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // Bias Detection Methods
  async getAvailableDatasets(): Promise<Dataset[]> {
    try {
      const response = await this.request<{ success: boolean; datasets: Dataset[] }>('/api/v1/bias/datasets/available')
      return response.datasets || []
    } catch (error) {
      console.error('Error fetching datasets:', error)
      // Return mock data for development
      return [
        {
          name: 'Credit Risk Dataset',
          samples: 10000,
          columns: ['age', 'income', 'credit_score', 'loan_amount', 'gender', 'race'],
          description: 'Credit risk assessment dataset'
        },
        {
          name: 'Fraud Detection Dataset',
          samples: 50000,
          columns: ['transaction_amount', 'location', 'time', 'user_id', 'device_type'],
          description: 'Financial fraud detection dataset'
        }
      ]
    }
  }

  async getDatasetInfo(datasetName: string): Promise<any> {
    const response = await this.request<{ success: boolean; dataset_info: any }>(`/bias/dataset-info/${datasetName}`)
    return response.dataset_info
  }

  async analyzeDatasetBias(request: BiasAnalysisRequest): Promise<BiasAnalysisResult> {
    const formData = new FormData()
    formData.append('dataset_name', request.dataset_name)
    formData.append('target_column', request.target_column)
    formData.append('sensitive_columns', JSON.stringify(request.sensitive_columns))
    formData.append('custom_rules', JSON.stringify(request.custom_rules || []))
    formData.append('llm_enabled', request.llm_enabled?.toString() || 'false')
    formData.append('llm_prompt', request.llm_prompt || '')
    formData.append('simulation_enabled', request.simulation_enabled?.toString() || 'false')

    const response = await fetch(`${this.baseURL}/api/v1/bias/analyze-real`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  async analyzeDatasetComprehensive(datasetName: string, targetColumn: string, sensitiveColumns: string[]): Promise<any> {
    const formData = new FormData()
    formData.append('dataset_name', datasetName)
    formData.append('target_column', targetColumn)
    formData.append('sensitive_columns', JSON.stringify(sensitiveColumns))

    const response = await fetch(`${this.baseURL}/api/v1/bias/analyze-comprehensive`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  async mitigateBias(datasetName: string, targetColumn: string, sensitiveColumns: string[], 
                    privilegedGroups: Record<string, any>, unprivilegedGroups: Record<string, any>): Promise<any> {
    const formData = new FormData()
    formData.append('dataset_name', datasetName)
    formData.append('target_column', targetColumn)
    formData.append('sensitive_columns', JSON.stringify(sensitiveColumns))
    formData.append('privileged_groups', JSON.stringify(privilegedGroups))
    formData.append('unprivileged_groups', JSON.stringify(unprivilegedGroups))

    const response = await fetch(`${this.baseURL}/bias/mitigate-bias`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    return result.data
  }

  async analyzeModelBias(modelId: string, datasetName: string, targetColumn: string, sensitiveColumns: string[]): Promise<any> {
    const response = await this.request<{ success: boolean; data: any }>('/bias/analyze-model', {
      method: 'POST',
      body: JSON.stringify({
        model_id: modelId,
        dataset_name: datasetName,
        target_column: targetColumn,
        sensitive_columns: sensitiveColumns
      })
    })
    return response.data
  }

  // Model Provenance Methods
  async createModelProvenance(request: ModelProvenanceRequest): Promise<ProvenanceResult> {
    const response = await this.request<{ success: boolean; data: ProvenanceResult }>('/provenance/model', {
      method: 'POST',
      body: JSON.stringify(request)
    })
    return response.data
  }

  async getModelProvenance(modelId: string): Promise<ProvenanceResult> {
    const response = await this.request<{ success: boolean; data: ProvenanceResult }>(`/provenance/model/${modelId}`)
    return response.data
  }

  async verifyModelSignature(modelId: string): Promise<{ valid: boolean; details: any }> {
    const response = await this.request<{ success: boolean; data: { valid: boolean; details: any } }>(`/provenance/verify/${modelId}`)
    return response.data
  }

  // Security & Compliance Methods
  async scanModelSecurity(request: SecurityScanRequest): Promise<SecurityScanResult> {
    const response = await this.request<{ success: boolean; data: SecurityScanResult }>('/security/scan', {
      method: 'POST',
      body: JSON.stringify(request)
    })
    return response.data
  }

  async getComplianceReport(modelId: string): Promise<any> {
    const response = await this.request<{ success: boolean; data: any }>(`/compliance/report/${modelId}`)
    return response.data
  }

  // Monitoring Methods
  async getModelMetrics(modelId: string): Promise<any> {
    const response = await this.request<{ success: boolean; data: any }>(`/monitoring/metrics/${modelId}`)
    return response.data
  }

  async getDriftAnalysis(modelId: string): Promise<any> {
    const response = await this.request<{ success: boolean; data: any }>(`/monitoring/drift/${modelId}`)
    return response.data
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request<{ status: string; version: string }>('/health')
  }
}

export const fairmindAPI = new FairmindAPI()
