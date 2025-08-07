import { 
  ApiResponse, 
  PaginatedResponse, 
  AIModel, 
  Simulation, 
  GovernanceMetric,
  AIBillRequirement,
  AIBillCompliance,
  AIMaterial,
  SimulationStatus,
  SimulationType
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;
  private headers: HeadersInit;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: this.headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<ApiResponse<{ token: string; user: any }>> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  // Models
  async getModels(page: number = 1, limit: number = 10): Promise<PaginatedResponse<AIModel>> {
    return this.request(`/models?page=${page}&limit=${limit}`);
  }

  async getModel(id: string): Promise<ApiResponse<AIModel>> {
    return this.request(`/models/${id}`);
  }

  async createModel(model: Partial<AIModel>): Promise<ApiResponse<AIModel>> {
    return this.request('/models', {
      method: 'POST',
      body: JSON.stringify(model),
    });
  }

  async updateModel(id: string, model: Partial<AIModel>): Promise<ApiResponse<AIModel>> {
    return this.request(`/models/${id}`, {
      method: 'PUT',
      body: JSON.stringify(model),
    });
  }

  async deleteModel(id: string): Promise<ApiResponse<void>> {
    return this.request(`/models/${id}`, {
      method: 'DELETE',
    });
  }

  // Simulations
  async getSimulations(
    page: number = 1, 
    limit: number = 10,
    status?: SimulationStatus,
    type?: SimulationType
  ): Promise<PaginatedResponse<Simulation>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (status) params.append('status', status);
    if (type) params.append('type', type);

    return this.request(`/simulations?${params.toString()}`);
  }

  async getSimulation(id: string): Promise<ApiResponse<Simulation>> {
    return this.request(`/simulations/${id}`);
  }

  async createSimulation(simulation: Partial<Simulation>): Promise<ApiResponse<Simulation>> {
    return this.request('/simulations', {
      method: 'POST',
      body: JSON.stringify(simulation),
    });
  }

  async updateSimulation(id: string, simulation: Partial<Simulation>): Promise<ApiResponse<Simulation>> {
    return this.request(`/simulations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(simulation),
    });
  }

  async deleteSimulation(id: string): Promise<ApiResponse<void>> {
    return this.request(`/simulations/${id}`, {
      method: 'DELETE',
    });
  }

  async startSimulation(id: string): Promise<ApiResponse<Simulation>> {
    return this.request(`/simulations/${id}/start`, {
      method: 'POST',
    });
  }

  async stopSimulation(id: string): Promise<ApiResponse<Simulation>> {
    return this.request(`/simulations/${id}/stop`, {
      method: 'POST',
    });
  }

  async getSimulationLogs(id: string): Promise<ApiResponse<any[]>> {
    return this.request(`/simulations/${id}/logs`);
  }

  // Governance Metrics
  async getGovernanceMetrics(): Promise<ApiResponse<GovernanceMetric[]>> {
    return this.request('/governance/metrics');
  }

  async getGovernanceMetric(id: string): Promise<ApiResponse<GovernanceMetric>> {
    return this.request(`/governance/metrics/${id}`);
  }

  async updateGovernanceMetric(id: string, metric: Partial<GovernanceMetric>): Promise<ApiResponse<GovernanceMetric>> {
    return this.request(`/governance/metrics/${id}`, {
      method: 'PUT',
      body: JSON.stringify(metric),
    });
  }

  // AI/ML Bill Requirements
  async getAIBillRequirements(): Promise<ApiResponse<AIBillRequirement[]>> {
    return this.request('/ai-bill/requirements');
  }

  async getAIBillRequirement(id: string): Promise<ApiResponse<AIBillRequirement>> {
    return this.request(`/ai-bill/requirements/${id}`);
  }

  async createAIBillRequirement(requirement: Partial<AIBillRequirement>): Promise<ApiResponse<AIBillRequirement>> {
    return this.request('/ai-bill/requirements', {
      method: 'POST',
      body: JSON.stringify(requirement),
    });
  }

  async updateAIBillRequirement(id: string, requirement: Partial<AIBillRequirement>): Promise<ApiResponse<AIBillRequirement>> {
    return this.request(`/ai-bill/requirements/${id}`, {
      method: 'PUT',
      body: JSON.stringify(requirement),
    });
  }

  async deleteAIBillRequirement(id: string): Promise<ApiResponse<void>> {
    return this.request(`/ai-bill/requirements/${id}`, {
      method: 'DELETE',
    });
  }

  // AI/ML Bill Compliance
  async getAIBillCompliance(requirementId?: string): Promise<ApiResponse<AIBillCompliance[]>> {
    const endpoint = requirementId 
      ? `/ai-bill/compliance?requirementId=${requirementId}`
      : '/ai-bill/compliance';
    return this.request(endpoint);
  }

  async getAIBillComplianceRecord(id: string): Promise<ApiResponse<AIBillCompliance>> {
    return this.request(`/ai-bill/compliance/${id}`);
  }

  async updateAIBillCompliance(id: string, compliance: Partial<AIBillCompliance>): Promise<ApiResponse<AIBillCompliance>> {
    return this.request(`/ai-bill/compliance/${id}`, {
      method: 'PUT',
      body: JSON.stringify(compliance),
    });
  }

  // AI/ML Materials
  async getAIMaterials(
    page: number = 1, 
    limit: number = 10,
    category?: string,
    type?: string
  ): Promise<PaginatedResponse<AIMaterial>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (category) params.append('category', category);
    if (type) params.append('type', type);

    return this.request(`/ai-bill/materials?${params.toString()}`);
  }

  async getAIMaterial(id: string): Promise<ApiResponse<AIMaterial>> {
    return this.request(`/ai-bill/materials/${id}`);
  }

  async createAIMaterial(material: Partial<AIMaterial>): Promise<ApiResponse<AIMaterial>> {
    return this.request('/ai-bill/materials', {
      method: 'POST',
      body: JSON.stringify(material),
    });
  }

  async updateAIMaterial(id: string, material: Partial<AIMaterial>): Promise<ApiResponse<AIMaterial>> {
    return this.request(`/ai-bill/materials/${id}`, {
      method: 'PUT',
      body: JSON.stringify(material),
    });
  }

  async deleteAIMaterial(id: string): Promise<ApiResponse<void>> {
    return this.request(`/ai-bill/materials/${id}`, {
      method: 'DELETE',
    });
  }

  // File Upload
  async uploadFile(file: File, type: string): Promise<ApiResponse<{ url: string; id: string }>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    return this.request('/upload', {
      method: 'POST',
      headers: {}, // Let browser set content-type for FormData
      body: formData,
    });
  }

  // Real-time Data
  async subscribeToSimulationUpdates(simulationId: string, callback: (data: any) => void): Promise<() => void> {
    // This would typically use WebSockets or Server-Sent Events
    // For now, we'll implement polling
    const interval = setInterval(async () => {
      try {
        const response = await this.getSimulation(simulationId);
        if (response.success && response.data) {
          callback(response.data);
        }
      } catch (error) {
        console.error('Error polling simulation updates:', error);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }

  // Analytics and Reports
  async getAnalytics(timeRange: string = '7d'): Promise<ApiResponse<any>> {
    return this.request(`/analytics?timeRange=${timeRange}`);
  }

  async generateReport(type: string, params: Record<string, any>): Promise<ApiResponse<{ reportUrl: string }>> {
    return this.request('/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ type, params }),
    });
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request('/health');
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();

// Export the class for testing or custom instances
export { ApiClient }; 