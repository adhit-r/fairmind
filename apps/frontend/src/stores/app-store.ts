import { create } from 'zustand';
import { 
  AIModel, 
  Dataset, 
  Simulation, 
  BiasAnalysisResult,
  BiasAnalysisConfig,
  SimulationConfig
} from '@/types';
import { fairmindAPI } from '@/lib/fairmind-api';

interface AppState {
  // Data
  models: AIModel[];
  datasets: Dataset[];
  simulations: Simulation[];
  biasAnalysis: BiasAnalysisResult | null;
  
  // UI State
  loading: Record<string, boolean>;
  errors: Record<string, string>;
  
  // Actions
  setModels: (models: AIModel[]) => void;
  setDatasets: (datasets: Dataset[]) => void;
  setSimulations: (simulations: Simulation[]) => void;
  setBiasAnalysis: (analysis: BiasAnalysisResult | null) => void;
  setLoading: (key: string, loading: boolean) => void;
  setError: (key: string, error: string) => void;
  clearError: (key: string) => void;
  
  // Async Actions
  fetchModels: (orgId?: string) => Promise<void>;
  fetchDatasets: (orgId?: string) => Promise<void>;
  fetchRecentSimulations: (orgId?: string, limit?: number) => Promise<void>;
  runBiasAnalysis: (config: BiasAnalysisConfig) => Promise<void>;
  runSimulation: (config: SimulationConfig) => Promise<void>;
  uploadModel: (file: File, metadata?: Partial<AIModel>) => Promise<void>;
  uploadDataset: (file: File) => Promise<void>;
  generateDataset: (config: {
    row_count: number;
    schema: { columns: Array<{ name: string; dtype: string }> };
    engine?: string;
  }) => Promise<{ path: string }>;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  models: [],
  datasets: [],
  simulations: [],
  biasAnalysis: null,
  loading: {},
  errors: {},

  // Synchronous actions
  setModels: (models) => set({ models }),
  setDatasets: (datasets) => set({ datasets }),
  setSimulations: (simulations) => set({ simulations }),
  setBiasAnalysis: (analysis) => set({ biasAnalysis: analysis }),
  
  setLoading: (key, loading) => set((state) => ({
    loading: { ...state.loading, [key]: loading }
  })),
  
  setError: (key, error) => set((state) => ({
    errors: { ...state.errors, [key]: error }
  })),
  
  clearError: (key) => set((state) => {
    const newErrors = { ...state.errors };
    delete newErrors[key];
    return { errors: newErrors };
  }),

  // Async actions
  fetchModels: async (orgId) => {
    const { setLoading, setError, setModels } = get();
    setLoading('models', true);
    setError('models', '');
    
    try {
      const models = await fairmindAPI.getModels(orgId);
      setModels(models);
    } catch (error) {
      setError('models', 'Failed to fetch models');
      console.error('Failed to fetch models:', error);
    } finally {
      setLoading('models', false);
    }
  },

  fetchDatasets: async (orgId) => {
    const { setLoading, setError, setDatasets } = get();
    setLoading('datasets', true);
    setError('datasets', '');
    
    try {
      const datasets = await fairmindAPI.getDatasets(orgId);
      setDatasets(datasets);
    } catch (error) {
      setError('datasets', 'Failed to fetch datasets');
      console.error('Failed to fetch datasets:', error);
    } finally {
      setLoading('datasets', false);
    }
  },

  fetchRecentSimulations: async (orgId, limit = 10) => {
    const { setLoading, setError, setSimulations } = get();
    setLoading('simulations', true);
    setError('simulations', '');
    
    try {
      const simulations = await fairmindAPI.getRecentSimulations(orgId, limit);
      setSimulations(simulations);
    } catch (error) {
      setError('simulations', 'Failed to fetch simulations');
      console.error('Failed to fetch simulations:', error);
    } finally {
      setLoading('simulations', false);
    }
  },

  runBiasAnalysis: async (config) => {
    const { setLoading, setError, setBiasAnalysis } = get();
    setLoading('biasAnalysis', true);
    setError('biasAnalysis', '');
    
    try {
      const result = await fairmindAPI.analyzeBias(config);
      setBiasAnalysis(result);
    } catch (error) {
      setError('biasAnalysis', 'Bias analysis failed');
      console.error('Bias analysis failed:', error);
      throw error;
    } finally {
      setLoading('biasAnalysis', false);
    }
  },

  runSimulation: async (config) => {
    const { setLoading, setError, fetchRecentSimulations } = get();
    setLoading('simulation', true);
    setError('simulation', '');
    
    try {
      await fairmindAPI.runSimulation(config);
      // Refresh simulations list after running
      await fetchRecentSimulations(config.org_id);
    } catch (error) {
      setError('simulation', 'Simulation failed');
      console.error('Simulation failed:', error);
      throw error;
    } finally {
      setLoading('simulation', false);
    }
  },

  uploadModel: async (file, metadata) => {
    const { setLoading, setError, fetchModels } = get();
    setLoading('modelUpload', true);
    setError('modelUpload', '');
    
    try {
      await fairmindAPI.uploadModel(file, metadata);
      // Refresh models list after upload
      await fetchModels();
    } catch (error) {
      setError('modelUpload', 'Model upload failed');
      console.error('Model upload failed:', error);
      throw error;
    } finally {
      setLoading('modelUpload', false);
    }
  },

  uploadDataset: async (file) => {
    const { setLoading, setError, fetchDatasets } = get();
    setLoading('datasetUpload', true);
    setError('datasetUpload', '');
    
    try {
      await fairmindAPI.uploadDataset(file);
      // Refresh datasets list after upload
      await fetchDatasets();
    } catch (error) {
      setError('datasetUpload', 'Dataset upload failed');
      console.error('Dataset upload failed:', error);
      throw error;
    } finally {
      setLoading('datasetUpload', false);
    }
  },

  generateDataset: async (config) => {
    const { setLoading, setError, fetchDatasets } = get();
    setLoading('datasetGeneration', true);
    setError('datasetGeneration', '');
    
    try {
      const result = await fairmindAPI.generateDataset(config);
      // Refresh datasets list after generation
      await fetchDatasets();
      return result;
    } catch (error) {
      setError('datasetGeneration', 'Dataset generation failed');
      console.error('Dataset generation failed:', error);
      throw error;
    } finally {
      setLoading('datasetGeneration', false);
    }
  },
}));
