import { 
  ApiResponse, 
  AIModel, 
  Simulation, 
  BiasAnalysisConfig,
  BiasAnalysisResult,
  Dataset,
  SimulationConfig
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class FairmindAPI {
  private static instance: FairmindAPI;
  private baseUrl: string;
  private headers: HeadersInit;

  private constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  static getInstance(): FairmindAPI {
    if (!FairmindAPI.instance) {
      FairmindAPI.instance = new FairmindAPI();
    }
    return FairmindAPI.instance;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: this.headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Models
  async getModels(orgId?: string): Promise<AIModel[]> {
    try {
      const endpoint = orgId ? `/models?org_id=${orgId}` : '/models';
      const response = await this.request<{ data: AIModel[] }>(endpoint);
      return response.data || [];
    } catch (error) {
      this.handleError(error, 'Failed to fetch models');
      return [];
    }
  }

  async uploadModel(file: File, metadata?: Partial<AIModel>): Promise<{ path: string; validation?: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (metadata?.framework) {
        formData.append('framework', metadata.framework);
      }
      if (metadata?.name) {
        formData.append('model_id', metadata.name);
      }

      const response = await fetch(`${this.baseUrl}/models/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Model upload failed');
      }

      return data;
    } catch (error) {
      this.handleError(error, 'Failed to upload model');
      throw error;
    }
  }

  // Datasets
  async getDatasets(orgId?: string): Promise<Dataset[]> {
    try {
      const endpoint = orgId ? `/datasets?org_id=${orgId}` : '/datasets';
      const response = await this.request<{ data: Dataset[] }>(endpoint);
      return response.data || [];
    } catch (error) {
      this.handleError(error, 'Failed to fetch datasets');
      return [];
    }
  }

  async uploadDataset(file: File): Promise<{ path: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/datasets/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Dataset upload failed');
      }

      return data;
    } catch (error) {
      this.handleError(error, 'Failed to upload dataset');
      throw error;
    }
  }

  async generateDataset(config: {
    row_count: number;
    schema: { columns: Array<{ name: string; dtype: string }> };
    engine?: string;
  }): Promise<{ path: string }> {
    try {
      const response = await this.request<{ path: string }>('/datasets/generate', {
        method: 'POST',
        body: JSON.stringify(config),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to generate dataset');
      throw error;
    }
  }

  // Bias Analysis
  async analyzeBias(config: BiasAnalysisConfig): Promise<BiasAnalysisResult> {
    try {
      const response = await this.request<BiasAnalysisResult>('/analyze/bias', {
        method: 'POST',
        body: JSON.stringify({
          model_path: config.modelPath,
          dataset_path: config.datasetPath,
          target: config.target,
          features: config.features,
          protected_attributes: config.protectedAttributes
        }),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Bias analysis failed');
      throw error;
    }
  }

  // Simulations
  async runSimulation(config: SimulationConfig): Promise<Simulation> {
    try {
      const response = await this.request<Simulation>('/simulation/run', {
        method: 'POST',
        body: JSON.stringify(config),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Simulation failed');
      throw error;
    }
  }

  async getRecentSimulations(orgId?: string, limit: number = 10): Promise<Simulation[]> {
    try {
      const endpoint = orgId ? `/simulations/recent?org_id=${orgId}&limit=${limit}` : `/simulations/recent?limit=${limit}`;
      const response = await this.request<Simulation[]>(endpoint);
      return response || [];
    } catch (error) {
      this.handleError(error, 'Failed to fetch recent simulations');
      return [];
    }
  }

  // Metrics
  async getMetricsSummary(orgId?: string): Promise<any> {
    try {
      const endpoint = orgId ? `/metrics/summary?company=${orgId}` : '/metrics/summary';
      const response = await this.request<any>(endpoint);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch metrics summary');
      return null;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await this.request<{ status: string }>('/health');
      return response;
    } catch (error) {
      this.handleError(error, 'Health check failed');
      throw error;
    }
  }

  // AI/ML Bill of Materials (BOM)
  async scanProjectBOM(request: {
    project_path: string;
    scan_type?: string;
    include_dev_dependencies?: boolean;
    include_transitive?: boolean;
    output_format?: string;
  }): Promise<any> {
    try {
      const response = await this.request<any>('/bom/scan', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'BOM scan failed');
      throw error;
    }
  }

  async getBOMDocuments(page: number = 1, limit: number = 10): Promise<any> {
    try {
      const response = await this.request<any>(`/bom/list?page=${page}&limit=${limit}`);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch BOM documents');
      throw error;
    }
  }

  async getBOMDocument(bomId: string): Promise<any> {
    try {
      const response = await this.request<any>(`/bom/${bomId}`);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch BOM document');
      throw error;
    }
  }

  async exportBOMDocument(bomId: string, format: string = 'json'): Promise<any> {
    try {
      const response = await this.request<any>(`/bom/export/${bomId}?format=${format}`, {
        method: 'POST'
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to export BOM document');
      throw error;
    }
  }

  async getBOMAnalysis(bomId: string): Promise<any> {
    try {
      const response = await this.request<any>(`/bom/analysis/${bomId}`);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch BOM analysis');
      throw error;
    }
  }

  async generateComprehensiveAIBOM(request: {
    project_path: string;
    scan_type?: string;
    include_dev_dependencies?: boolean;
    include_transitive?: boolean;
    output_format?: string;
  }): Promise<any> {
    try {
      const response = await this.request<any>('/bom/generate-comprehensive', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to generate comprehensive AIBOM');
      throw error;
    }
  }

  // OWASP Top 10 AI/LLM Security Methods
  async getOWASPTests(): Promise<any> {
    try {
      const response = await this.request<any>('/owasp/tests');
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch OWASP tests');
      throw error;
    }
  }

  async getOWASPCategories(): Promise<any> {
    try {
      const response = await this.request<any>('/owasp/categories');
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch OWASP categories');
      throw error;
    }
  }

  async getOWASPModelInventory(): Promise<any> {
    try {
      const response = await this.request<any>('/owasp/models');
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch OWASP model inventory');
      throw error;
    }
  }

  async runOWASPSecurityAnalysis(request: {
    model_id: string;
    test_categories?: string[];
    include_all_tests?: boolean;
    test_parameters?: Record<string, any>;
    priority?: string;
  }): Promise<any> {
    try {
      const response = await this.request<any>('/owasp/analyze', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to run OWASP security analysis');
      throw error;
    }
  }

  async getOWASPSecurityAnalysis(analysisId: string): Promise<any> {
    try {
      const response = await this.request<any>(`/owasp/analysis/${analysisId}`);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch OWASP security analysis');
      throw error;
    }
  }

  async listOWASPSecurityAnalyses(page: number = 1, limit: number = 10): Promise<any> {
    try {
      const response = await this.request<any>(`/owasp/analysis?page=${page}&limit=${limit}`);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to list OWASP security analyses');
      throw error;
    }
  }

  // Bias Analysis Methods
  async runBiasAnalysis(request: {
    model_id: string
    dataset_id: string
    sensitive_attributes: string[]
    target_column: string
    analysis_type: 'comprehensive' | 'quick' | 'targeted'
  }): Promise<any> {
    try {
      const response = await this.request<any>('/bias/analyze', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to run bias analysis');
      throw error;
    }
  }

  async getBiasAnalysisHistory(): Promise<any> {
    try {
      const response = await this.request<any>('/bias/history');
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch bias analysis history');
      throw error;
    }
  }

  // Dashboard Methods
  async getRecentActivity(limit: number = 10): Promise<any> {
    try {
      const response = await this.request<any>(`/activity/recent?limit=${limit}`);
      return response;
    } catch (error) {
      this.handleError(error, 'Failed to fetch recent activity');
      throw error;
    }
  }

  // Real Bias Detection Methods
  async getAvailableDatasets(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets/available`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching available datasets:', error);
      throw error;
    }
  }

  async analyzeDatasetBias(params: {
    dataset_name: string;
    target_column: string;
    sensitive_columns: string[];
    custom_rules?: any[];
    llm_enabled?: boolean;
    llm_prompt?: string;
    simulation_enabled?: boolean;
  }): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('dataset_name', params.dataset_name);
      formData.append('target_column', params.target_column);
      formData.append('sensitive_columns', JSON.stringify(params.sensitive_columns));
      formData.append('custom_rules', JSON.stringify(params.custom_rules || []));
      formData.append('llm_enabled', String(params.llm_enabled || false));
      formData.append('llm_prompt', params.llm_prompt || '');
      formData.append('simulation_enabled', String(params.simulation_enabled || false));

      const response = await fetch(`${this.baseUrl}/bias/analyze-real`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error analyzing dataset bias:', error);
      throw error;
    }
  }

  async getDatasetInfo(datasetName: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/bias/dataset-info/${datasetName}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching dataset info:', error);
      throw error;
    }
  }

  // Model Provenance and Model Cards Methods
  async createDatasetProvenance(datasetInfo: any): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/dataset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(datasetInfo),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error creating dataset provenance:', error);
      throw error;
    }
  }

  async createModelProvenance(modelInfo: any, trainingDatasets: any[]): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/model`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_info: modelInfo,
          training_datasets: trainingDatasets
        }),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error creating model provenance:', error);
      throw error;
    }
  }

  async scanModel(modelPath: string, modelInfo: any): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/scan-model`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_path: modelPath,
          model_info: modelInfo
        }),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error scanning model:', error);
      throw error;
    }
  }

  async verifyModelAuthenticity(modelId: string, modelContent: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/verify-authenticity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: modelId,
          model_content: modelContent
        }),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error verifying model authenticity:', error);
      throw error;
    }
  }

  async generateModelCard(modelId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/model-card/${modelId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error generating model card:', error);
      throw error;
    }
  }

  async getProvenanceChain(modelId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/chain/${modelId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting provenance chain:', error);
      throw error;
    }
  }

  async exportProvenanceReport(modelId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/report/${modelId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error exporting provenance report:', error);
      throw error;
    }
  }

  async listProvenanceModels(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/provenance/models`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error listing provenance models:', error);
      throw error;
    }
  }

  private handleError(error: unknown, message: string): void {
    console.error(message, error);
    // Could integrate with error reporting service here
    // Could also dispatch to a global error store
  }
}

// Export singleton instance
export const fairmindAPI = FairmindAPI.getInstance();
