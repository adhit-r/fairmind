import { useCallback, useEffect } from 'react';
import { useAppStore } from '@/stores/app-store';
import { BiasAnalysisConfig } from '@/types';
import { useAuth } from '@/contexts/auth-context';

export function useBiasAnalysis() {
  const { profile } = useAuth();
  const orgId = profile?.default_org_id || null;
  
  const {
    models,
    datasets,
    biasAnalysis,
    loading,
    errors,
    fetchModels,
    fetchDatasets,
    runBiasAnalysis,
    setBiasAnalysis,
    setError,
    clearError
  } = useAppStore();

  // Load models and datasets on mount
  useEffect(() => {
    if (orgId) {
      fetchModels(orgId);
      fetchDatasets(orgId);
    }
  }, [orgId, fetchModels, fetchDatasets]);

  const analyzeBias = useCallback(async (config: BiasAnalysisConfig) => {
    if (!config.modelPath || !config.datasetPath || !config.target || !config.features.length) {
      setError('biasAnalysis', 'Please provide all required configuration');
      return;
    }

    try {
      await runBiasAnalysis(config);
    } catch (error) {
      // Error is already handled in the store
      console.error('Bias analysis failed:', error);
    }
  }, [runBiasAnalysis, setError]);

  const clearAnalysis = useCallback(() => {
    setBiasAnalysis(null);
    clearError('biasAnalysis');
  }, [setBiasAnalysis, clearError]);

  return {
    // Data
    models,
    datasets,
    biasAnalysis,
    
    // State
    loading: loading.biasAnalysis || loading.models || loading.datasets,
    error: errors.biasAnalysis,
    
    // Actions
    analyzeBias,
    clearAnalysis,
    
    // Auto-population helpers
    autoPopulateFromDataset: (datasetPath: string) => {
      const dataset = datasets.find(d => d.path === datasetPath);
      if (dataset?.columns && dataset.columns.length > 0) {
        return {
          features: dataset.columns.slice(0, -1).join(','),
          target: dataset.columns[dataset.columns.length - 1]
        };
      }
      return null;
    }
  };
}
