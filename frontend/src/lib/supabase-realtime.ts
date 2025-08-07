import React from 'react';
import { createClient } from '@supabase/supabase-js';
import { GovernanceMetric, AIModel, Simulation, AIBillRequirement } from '@/types';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://localhost:54321';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'your-anon-key';

export const supabase = createClient(supabaseUrl, supabaseKey);

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

class SupabaseRealTimeService {
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  private isConnected = false;
  private retryCount = 0;
  private maxRetries = 3;

  constructor() {
    this.initializeRealtime();
  }

  private async initializeRealtime() {
    try {
      // Subscribe to real-time changes
      const governanceMetricsChannel = supabase
        .channel('governance_metrics')
        .on('postgres_changes', 
          { event: '*', schema: 'public', table: 'governance_metrics' },
          (payload) => {
            this.publish('governance_metrics', payload.new);
          }
        )
        .subscribe();

      const modelsChannel = supabase
        .channel('models')
        .on('postgres_changes', 
          { event: '*', schema: 'public', table: 'models' },
          (payload) => {
            this.publish('models', payload.new);
          }
        )
        .subscribe();

      const simulationsChannel = supabase
        .channel('simulations')
        .on('postgres_changes', 
          { event: '*', schema: 'public', table: 'simulations' },
          (payload) => {
            this.publish('simulations', payload.new);
          }
        )
        .subscribe();

      const aiBillChannel = supabase
        .channel('ai_bill_requirements')
        .on('postgres_changes', 
          { event: '*', schema: 'public', table: 'ai_bill_requirements' },
          (payload) => {
            this.publish('ai_bill', payload.new);
          }
        )
        .subscribe();

      this.isConnected = true;
      this.retryCount = 0;
      console.log('Supabase real-time service initialized');

    } catch (error) {
      console.error('Failed to initialize Supabase real-time:', error);
      this.handleConnectionError();
    }
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

  // Handle connection errors and retry
  private handleConnectionError(): void {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      console.log(`Retrying Supabase connection in 5s (attempt ${this.retryCount})`);
      
      setTimeout(() => {
        if (!this.isConnected) {
          this.initializeRealtime();
        }
      }, 5000);
    } else {
      console.error('Max retry attempts reached for Supabase real-time');
    }
  }

  // Get current connection status
  getConnectionStatus(): { isConnected: boolean; type: 'supabase' | 'disconnected' } {
    return {
      isConnected: this.isConnected,
      type: this.isConnected ? 'supabase' : 'disconnected'
    };
  }

  // Manual data refresh from API
  async refreshData(): Promise<void> {
    try {
      // Fetch data from Python API
      const [governanceMetrics, models, simulations, aiBillRequirements] = await Promise.all([
        this.fetchGovernanceMetrics(),
        this.fetchModels(),
        this.fetchSimulations(),
        this.fetchAIBillRequirements()
      ]);

      // Calculate compliance status
      const complianceStatus = this.calculateComplianceStatus(
        governanceMetrics,
        models
      );

      // Publish updates
      this.publish('governance_metrics', governanceMetrics);
      this.publish('models', models);
      this.publish('simulations', simulations);
      this.publish('compliance', complianceStatus);
      this.publish('ai_bill', aiBillRequirements);
      this.publish('dashboard', {
        governanceMetrics,
        activeModels: models,
        recentSimulations: simulations,
        complianceStatus,
        aiBillRequirements,
        lastUpdated: new Date()
      });

    } catch (error) {
      console.error('Error refreshing data:', error);
      throw error;
    }
  }

  // Fetch data from Python API
  private async fetchGovernanceMetrics(): Promise<GovernanceMetric[]> {
    const response = await fetch('http://localhost:8000/governance/metrics');
    const data = await response.json();
    return data.data || [];
  }

  private async fetchModels(): Promise<AIModel[]> {
    const response = await fetch('http://localhost:8000/models');
    const data = await response.json();
    return data.data || [];
  }

  private async fetchSimulations(): Promise<Simulation[]> {
    const response = await fetch('http://localhost:8000/simulations');
    const data = await response.json();
    return data.data || [];
  }

  private async fetchAIBillRequirements(): Promise<AIBillRequirement[]> {
    const response = await fetch('http://localhost:8000/ai-bill/requirements');
    const data = await response.json();
    return data.data || [];
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

  // Stop real-time service
  stop(): void {
    this.isConnected = false;
    supabase.removeAllChannels();
    console.log('Supabase real-time service stopped');
  }
}

// Create singleton instance
export const supabaseRealTimeService = new SupabaseRealTimeService();

// React hook for real-time data
export function useSupabaseRealTimeData<T>(channel: string, initialData?: T) {
  const [data, setData] = React.useState<T | undefined>(initialData);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const unsubscribe = supabaseRealTimeService.subscribe(channel, (newData: T) => {
      setData(newData);
      setIsLoading(false);
      setError(null);
    });

    // Initial data fetch
    supabaseRealTimeService.refreshData().catch(err => {
      setError(err);
      setIsLoading(false);
    });

    return unsubscribe;
  }, [channel]);

  return { data, isLoading, error };
}

// Dashboard-specific hooks
export function useDashboardData() {
  return useSupabaseRealTimeData<RealTimeData>('dashboard');
}

export function useGovernanceMetrics() {
  return useSupabaseRealTimeData<GovernanceMetric[]>('governance_metrics', []);
}

export function useActiveModels() {
  return useSupabaseRealTimeData<AIModel[]>('models', []);
}

export function useRecentSimulations() {
  return useSupabaseRealTimeData<Simulation[]>('simulations', []);
}

export function useComplianceStatus() {
  return useSupabaseRealTimeData<RealTimeData['complianceStatus']>('compliance', {
    nistCompliance: 82,
    activeModels: 47,
    criticalRisks: 3,
    llmSafetyScore: 88
  });
}

export function useAIBillRequirements() {
  return useSupabaseRealTimeData<AIBillRequirement[]>('ai_bill', []);
} 