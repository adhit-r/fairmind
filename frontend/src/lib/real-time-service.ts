import React from 'react';
import { apiClient } from './api-client';
import { GovernanceMetric, AIModel, Simulation, AIBillRequirement } from '@/types';

export interface RealTimeData {
  governanceMetrics: GovernanceMetric[];
  activeModels: AIModel[];
  recentSimulations: Simulation[];
  complianceStatus: {
    nistCompliance: number;
    activeModels: number;
    criticalRisks: number;
    llmSafetyScore: number;
  };
  aiBillRequirements: AIBillRequirement[];
  lastUpdated: Date;
}

export interface RealTimeConfig {
  pollingInterval: number; // milliseconds
  enableWebSocket: boolean;
  enablePolling: boolean;
  retryAttempts: number;
  retryDelay: number;
}

class RealTimeService {
  private config: RealTimeConfig;
  private pollingTimer: NodeJS.Timeout | null = null;
  private websocket: WebSocket | null = null;
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  private isConnected = false;
  private retryCount = 0;

  constructor(config: Partial<RealTimeConfig> = {}) {
    this.config = {
      pollingInterval: 30000, // 30 seconds
      enableWebSocket: true,
      enablePolling: true,
      retryAttempts: 3,
      retryDelay: 5000,
      ...config,
    };
  }

  // Start real-time updates
  async start(): Promise<void> {
    try {
      if (this.config.enableWebSocket) {
        await this.connectWebSocket();
      }
      
      if (this.config.enablePolling) {
        this.startPolling();
      }
      
      this.isConnected = true;
      console.log('Real-time service started');
    } catch (error) {
      console.error('Failed to start real-time service:', error);
      this.handleConnectionError();
    }
  }

  // Stop real-time updates
  stop(): void {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
    
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    
    this.isConnected = false;
    console.log('Real-time service stopped');
  }

  // Subscribe to real-time updates
  subscribe<T>(channel: string, callback: (data: T) => void): () => void {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set());
    }
    
    this.subscribers.get(channel)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const channelSubscribers = this.subscribers.get(channel);
      if (channelSubscribers) {
        channelSubscribers.delete(callback);
        if (channelSubscribers.size === 0) {
          this.subscribers.delete(channel);
        }
      }
    };
  }

  // Publish data to subscribers
  private publish<T>(channel: string, data: T): void {
    const channelSubscribers = this.subscribers.get(channel);
    if (channelSubscribers) {
      channelSubscribers.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in subscriber callback:', error);
        }
      });
    }
  }

  // WebSocket connection
  private async connectWebSocket(): Promise<void> {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    
    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
          console.log('WebSocket connected');
          this.retryCount = 0;
          resolve();
        };
        
        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
        
        this.websocket.onclose = () => {
          console.log('WebSocket disconnected');
          this.handleConnectionError();
        };
        
      } catch (error) {
        reject(error);
      }
    });
  }

  // Handle WebSocket messages
  private handleWebSocketMessage(data: any): void {
    const { type, payload } = data;
    
    switch (type) {
      case 'governance_metrics_update':
        this.publish('governance_metrics', payload);
        break;
      case 'model_status_update':
        this.publish('models', payload);
        break;
      case 'simulation_progress':
        this.publish('simulations', payload);
        break;
      case 'compliance_update':
        this.publish('compliance', payload);
        break;
      case 'ai_bill_update':
        this.publish('ai_bill', payload);
        break;
      default:
        console.warn('Unknown WebSocket message type:', type);
    }
  }

  // Polling mechanism
  private startPolling(): void {
    this.pollingTimer = setInterval(async () => {
      try {
        await this.fetchAllData();
      } catch (error) {
        console.error('Polling error:', error);
        this.handleConnectionError();
      }
    }, this.config.pollingInterval);
  }

  // Fetch all dashboard data
  private async fetchAllData(): Promise<void> {
    try {
      const [
        governanceMetrics,
        models,
        simulations,
        aiBillRequirements
      ] = await Promise.all([
        apiClient.getGovernanceMetrics(),
        apiClient.getModels(1, 10),
        apiClient.getSimulations(1, 5),
        apiClient.getAIBillRequirements()
      ]);

      // Calculate compliance status
      const complianceStatus = this.calculateComplianceStatus(
        governanceMetrics.data || [],
        models.data || []
      );

      // Publish updates
      this.publish('governance_metrics', governanceMetrics.data || []);
      this.publish('models', models.data || []);
      this.publish('simulations', simulations.data || []);
      this.publish('compliance', complianceStatus);
      this.publish('ai_bill', aiBillRequirements.data || []);
      this.publish('dashboard', {
        governanceMetrics: governanceMetrics.data || [],
        activeModels: models.data || [],
        recentSimulations: simulations.data || [],
        complianceStatus,
        aiBillRequirements: aiBillRequirements.data || [],
        lastUpdated: new Date()
      });

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }

  // Calculate compliance status from metrics
  private calculateComplianceStatus(
    metrics: GovernanceMetric[],
    models: AIModel[]
  ): RealTimeData['complianceStatus'] {
    const nistMetrics = metrics.filter(m => m.category === 'COMPLIANCE');
    const fairnessMetrics = metrics.filter(m => m.category === 'FAIRNESS');
    const safetyMetrics = metrics.filter(m => m.category === 'LLM_SAFETY');
    
    const nistCompliance = nistMetrics.length > 0 
      ? nistMetrics.reduce((sum, m) => sum + m.value, 0) / nistMetrics.length 
      : 82;
    
    const activeModels = models.filter(m => m.status === 'ACTIVE').length;
    
    const criticalRisks = metrics.filter(m => m.status === 'CRITICAL').length;
    
    const llmSafetyScore = safetyMetrics.length > 0
      ? safetyMetrics.reduce((sum, m) => sum + m.value, 0) / safetyMetrics.length
      : 88;

    return {
      nistCompliance: Math.round(nistCompliance),
      activeModels,
      criticalRisks,
      llmSafetyScore: Math.round(llmSafetyScore)
    };
  }

  // Handle connection errors and retry
  private handleConnectionError(): void {
    if (this.retryCount < this.config.retryAttempts) {
      this.retryCount++;
      console.log(`Retrying connection in ${this.config.retryDelay}ms (attempt ${this.retryCount})`);
      
      setTimeout(() => {
        if (this.isConnected) {
          this.start();
        }
      }, this.config.retryDelay);
    } else {
      console.error('Max retry attempts reached, falling back to polling only');
      this.config.enableWebSocket = false;
      this.startPolling();
    }
  }

  // Get current connection status
  getConnectionStatus(): { isConnected: boolean; type: 'websocket' | 'polling' | 'disconnected' } {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      return { isConnected: true, type: 'websocket' };
    } else if (this.pollingTimer) {
      return { isConnected: true, type: 'polling' };
    } else {
      return { isConnected: false, type: 'disconnected' };
    }
  }

  // Manual data refresh
  async refreshData(): Promise<void> {
    await this.fetchAllData();
  }
}

// Create singleton instance
export const realTimeService = new RealTimeService();

// React hook for real-time data
export function useRealTimeData<T>(channel: string, initialData?: T) {
  const [data, setData] = React.useState<T | undefined>(initialData);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const unsubscribe = realTimeService.subscribe(channel, (newData: T) => {
      setData(newData);
      setIsLoading(false);
      setError(null);
    });

    // Initial data fetch
    realTimeService.refreshData().catch(err => {
      setError(err);
      setIsLoading(false);
    });

    return unsubscribe;
  }, [channel]);

  return { data, isLoading, error };
}

// Dashboard-specific hooks
export function useDashboardData() {
  return useRealTimeData<RealTimeData>('dashboard');
}

export function useGovernanceMetrics() {
  return useRealTimeData<GovernanceMetric[]>('governance_metrics', []);
}

export function useActiveModels() {
  return useRealTimeData<AIModel[]>('models', []);
}

export function useRecentSimulations() {
  return useRealTimeData<Simulation[]>('simulations', []);
}

export function useComplianceStatus() {
  return useRealTimeData<RealTimeData['complianceStatus']>('compliance', {
    nistCompliance: 82,
    activeModels: 47,
    criticalRisks: 3,
    llmSafetyScore: 88
  });
}

export function useAIBillRequirements() {
  return useRealTimeData<AIBillRequirement[]>('ai_bill', []);
} 