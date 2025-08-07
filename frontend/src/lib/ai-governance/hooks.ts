/**
 * React hooks for AI Governance features
 */

import { useState, useCallback, useEffect } from 'react';
import { 
  aiGovernanceClient, 
  BiasAnalysisRequest, 
  BiasAnalysisResponse,
  ExplanationResponse,
  NISTComplianceResponse,
  DriftDetectionResponse
} from './client';

export function useBiasAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<BiasAnalysisResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const analyzeBias = useCallback(async (request: BiasAnalysisRequest) => {
    setIsAnalyzing(true);
    setError(null);
    
    try {
      const result = await aiGovernanceClient.analyzeBias(request);
      setAnalysisResult(result);
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  return {
    analyzeBias,
    isAnalyzing,
    analysisResult,
    error,
  };
}

export function useModelExplanation() {
  const [isExplaining, setIsExplaining] = useState(false);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const explainModel = useCallback(async (modelId: string, predictionData: Record<string, unknown>) => {
    setIsExplaining(true);
    setError(null);
    
    try {
      const result = await aiGovernanceClient.explainModel(modelId, predictionData);
      setExplanation(result);
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setIsExplaining(false);
    }
  }, []);

  return {
    explainModel,
    isExplaining,
    explanation,
    error,
  };
}

export function useNISTCompliance() {
  const [isCalculating, setIsCalculating] = useState(false);
  const [complianceResult, setComplianceResult] = useState<NISTComplianceResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const calculateCompliance = useCallback(async (modelId: string, assessmentData: Record<string, unknown>) => {
    setIsCalculating(true);
    setError(null);
    
    try {
      const result = await aiGovernanceClient.calculateNISTCompliance(modelId, assessmentData);
      setComplianceResult(result);
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setIsCalculating(false);
    }
  }, []);

  return {
    calculateCompliance,
    isCalculating,
    complianceResult,
    error,
  };
}

export function useDriftDetection() {
  const [isDetecting, setIsDetecting] = useState(false);
  const [driftResult, setDriftResult] = useState<DriftDetectionResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const detectDrift = useCallback(async (
    modelId: string, 
    currentData: Record<string, unknown>[], 
    referenceData: Record<string, unknown>[]
  ) => {
    setIsDetecting(true);
    setError(null);
    
    try {
      const result = await aiGovernanceClient.detectDrift(modelId, currentData, referenceData);
      setDriftResult(result);
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setIsDetecting(false);
    }
  }, []);

  return {
    detectDrift,
    isDetecting,
    driftResult,
    error,
  };
}

export function useMLServiceHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [healthData, setHealthData] = useState<Record<string, unknown> | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkHealth = useCallback(async () => {
    setIsChecking(true);
    
    try {
      const result = await aiGovernanceClient.healthCheck();
      setHealthData(result);
      setIsHealthy(true);
      return result;
    } catch (error) {
      console.error('ML service health check failed:', error);
      setIsHealthy(false);
      throw error;
    } finally {
      setIsChecking(false);
    }
  }, []);

  // Check health on mount
  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return {
    isHealthy,
    healthData,
    isChecking,
    checkHealth,
  };
}
