// API Configuration - Real data integration for FairMind
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

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
    category: string
    status: 'passed' | 'failed' | 'skipped'
    severity: 'critical' | 'high' | 'medium' | 'low'
    description: string
    recommendation: string
    executionTime: number
  }>
}

interface SecurityTest {
  id: string
  name: string
  category: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  enabled: boolean
  lastRun?: string
  status?: 'passed' | 'failed' | 'skipped'
}

// Model Registry Types
interface Model {
  id: string
  name: string
  version: string
  type: 'llm' | 'classic_ml' | 'deep_learning'
  status: 'active' | 'inactive' | 'deprecated'
  accuracy: number
  biasScore: number
  securityScore: number
  lastUpdated: string
  description: string
  tags: string[]
}

interface Dataset {
  id: string
  name: string
  type: 'training' | 'validation' | 'test'
  size: number
  records: number
  features: number
  lastUpdated: string
  description: string
  tags: string[]
}

// AI BOM Types
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

// Compliance Types
interface ComplianceFramework {
  id: string
  name: string
  type: string
  status: string
  complianceScore: number
  lastAssessment: string
  nextReview: string
}

interface ComplianceProject {
  id: string
  name: string
  type: string
  status: string
  progress: number
  framework: string
  owner: string
  dueDate: string
}

interface AttestationResult {
  id: string
  name: string
  type: string
  framework: string
  status: string
  score: number
  auditDate: string
  expiryDate: string
}

// Governance Types
interface GovernancePolicy {
  id: string
  name: string
  category: string
  status: string
  priority: string
  complianceRate: number
  effectiveness: number
  violations: number
  enforcement: string
}

interface GovernanceEvent {
  id: string
  timestamp: string
  type: string
  severity: string
  description: string
  affectedPolicy: string
  status: string
  automated: boolean
}

// Regulatory Mapping Types
interface RegulatoryMapping {
  id: string
  frameworkName: string
  requirementName: string
  mappedControls: string[]
  mappingStrength: string
  lastMapped: string
  mappedBy: string
}

// Report Types
interface ReportTemplate {
  id: string
  name: string
  type: string
  description: string
  sections: string[]
  lastUsed: string
  usageCount: number
}

interface GeneratedReport {
  id: string
  name: string
  type: string
  status: string
  author: string
  createdAt: string
  lastUpdated: string
  audience: string[]
  score: number
}

class ApiClient {
  private baseUrl: string;
  
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data: data,
      };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // Dashboard Methods - Real data integration
  async getGovernanceMetrics(): Promise<ApiResponse<GovernanceMetrics>> {
    return this.request<GovernanceMetrics>('/api/v1/governance/metrics');
  }

  async getRecentActivity(): Promise<ApiResponse<RecentActivity[]>> {
    return this.request<RecentActivity[]>('/api/v1/activity/recent');
  }

  async getMetricsSummary(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/metrics/summary');
  }

  // Bias Detection Methods - Real data integration
  async getBiasDatasets(): Promise<ApiResponse<Dataset[]>> {
    return this.request<Dataset[]>('/api/v1/bias/datasets');
  }

  async getModels(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/api/v1/models');
  }

  async analyzeBias(request: BiasAnalysisRequest): Promise<ApiResponse<BiasAnalysisResult>> {
    return this.request<BiasAnalysisResult>('/api/v1/bias/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async analyzeBiasClassic(request: BiasAnalysisRequest): Promise<ApiResponse<BiasAnalysisResult>> {
    return this.request<BiasAnalysisResult>('/api/v1/bias/analyze-classic', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async analyzeBiasReal(request: BiasAnalysisRequest): Promise<ApiResponse<BiasAnalysisResult>> {
    return this.request<BiasAnalysisResult>('/api/v1/bias/analyze-real', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getBiasAnalysisHistory(): Promise<ApiResponse<BiasAnalysisResult[]>> {
    return this.request<BiasAnalysisResult[]>('/api/v1/bias/analysis');
  }

  async getExplainabilityTools(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/bias/explainability-tools');
  }

  // Security Testing Methods - Real data integration
  async runSecurityAnalysis(request: SecurityTestRequest): Promise<ApiResponse<SecurityAnalysisResult>> {
    return this.request<SecurityAnalysisResult>('/api/v1/security/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getSecurityTestHistory(): Promise<ApiResponse<SecurityAnalysisResult[]>> {
    return this.request<SecurityAnalysisResult[]>('/api/v1/security/history');
  }

  async getSecurityTests(): Promise<ApiResponse<SecurityTest[]>> {
    return this.request<SecurityTest[]>('/api/v1/security/tests');
  }

  async getOWASPCategories(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/api/v1/security/owasp-categories');
  }

  // Model Registry Methods - Real data integration
  async getModelRegistry(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/api/v1/models');
  }

  async registerModel(model: Partial<Model>): Promise<ApiResponse<Model>> {
    return this.request<Model>('/api/v1/models', {
      method: 'POST',
      body: JSON.stringify(model),
    });
  }

  async uploadModel(formData: FormData): Promise<Response> {
    const url = `${this.baseUrl}/api/v1/models`;
    return fetch(url, {
      method: 'POST',
      body: formData,
    });
  }

  // Dataset Management Methods - Real data integration
  async uploadDataset(file: File): Promise<ApiResponse<Dataset>> {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = `${this.baseUrl}/api/v1/datasets`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      success: true,
      data: data,
    };
  }

  async getAvailableDatasets(): Promise<ApiResponse<Dataset[]>> {
    return this.request<Dataset[]>('/api/v1/datasets');
  }

  // AI BOM Methods - Real data integration
  async scanBOM(request: any): Promise<ApiResponse<BOMDocument>> {
    return this.request<BOMDocument>('/api/v1/bom/scan', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getBOMList(): Promise<ApiResponse<BOMDocument[]>> {
    return this.request<BOMDocument[]>('/api/v1/bom/list');
  }

  async getBOMById(bomId: string): Promise<ApiResponse<BOMDocument>> {
    return this.request<BOMDocument>(`/api/v1/bom/${bomId}`);
  }

  async generateComprehensiveBOM(request: any): Promise<ApiResponse<BOMDocument>> {
    return this.request<BOMDocument>('/api/v1/bom/generate-comprehensive', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Monitoring Methods - Real data integration
  async getMonitoringMetrics(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/monitoring/metrics');
  }

  async getDriftAnalysis(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/monitoring/drift');
  }

  // Compliance Methods - Real data integration
  async getComplianceFrameworks(): Promise<ApiResponse<ComplianceFramework[]>> {
    return this.request<ComplianceFramework[]>('/api/v1/compliance/frameworks');
  }

  async getComplianceProjects(): Promise<ApiResponse<ComplianceProject[]>> {
    return this.request<ComplianceProject[]>('/api/v1/compliance/projects');
  }

  async getAttestationResults(): Promise<ApiResponse<AttestationResult[]>> {
    return this.request<AttestationResult[]>('/api/v1/attestation/results');
  }

  async getNISTComplianceScore(request: any): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/compliance/nist-score', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Governance Methods - Real data integration
  async getGovernancePolicies(): Promise<ApiResponse<GovernancePolicy[]>> {
    return this.request<GovernancePolicy[]>('/api/v1/governance/policies');
  }

  async getGovernanceEvents(): Promise<ApiResponse<GovernanceEvent[]>> {
    return this.request<GovernanceEvent[]>('/api/v1/governance/events');
  }

  // Regulatory Mapping Methods - Real data integration
  async getRegulatoryMapping(): Promise<ApiResponse<RegulatoryMapping[]>> {
    return this.request<RegulatoryMapping[]>('/api/v1/regulatory/mapping');
  }

  // Report Methods - Real data integration
  async getReportTemplates(): Promise<ApiResponse<ReportTemplate[]>> {
    return this.request<ReportTemplate[]>('/api/v1/reports/templates');
  }

  async getGeneratedReports(): Promise<ApiResponse<GeneratedReport[]>> {
    return this.request<GeneratedReport[]>('/api/v1/reports/generated');
  }

  // Provenance Methods - Real data integration
  async getProvenanceModels(): Promise<ApiResponse<Model[]>> {
    return this.request<Model[]>('/api/v1/provenance/models');
  }

  async getProvenanceModelCard(modelId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/provenance/model-card/${modelId}`);
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }
}

export const api = new ApiClient(API_BASE_URL);

// Export types for use in components
export type {
  ApiResponse,
  GovernanceMetrics,
  RecentActivity,
  BiasAnalysisRequest,
  BiasAnalysisResult,
  SecurityTestRequest,
  SecurityAnalysisResult,
  SecurityTest,
  Model,
  Dataset,
  BOMDocument,
  BOMComponent,
  ComplianceFramework,
  ComplianceProject,
  AttestationResult,
  GovernancePolicy,
  GovernanceEvent,
  RegulatoryMapping,
  ReportTemplate,
  GeneratedReport,
};
