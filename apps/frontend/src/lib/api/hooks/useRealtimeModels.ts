import { useState, useCallback } from 'react';
import { apiClient, type ApiResponse } from '../api-client';
import { API_ENDPOINTS } from '../endpoints';

export interface ModelConfig {
    provider: string;
    model_name: string;
    model_type: string;
    api_key?: string;
    base_url?: string;
    max_tokens?: number;
    temperature?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    timeout?: number;
    retry_attempts?: number;
}

export interface BiasTestResult {
    success: boolean;
    test_type: string;
    prompt: string;
    model_response: {
        provider: string;
        model_name: string;
        response_text: string;
        tokens_used: number;
        response_time: number;
        timestamp: string;
        metadata?: any;
    };
    bias_score: number;
    bias_indicators_found: string[];
    protected_attributes_affected: string[];
    confidence_score: number;
    explanation: string;
    recommendations: string[];
    timestamp: string;
}

export interface ComprehensiveAnalysisResult {
    success: boolean;
    analysis_id: string;
    timestamp: string;
    model_name: string;
    provider: string;
    tests_performed: string[];
    overall_bias_score: number;
    test_results: any[];
    risk_assessment: any;
    recommendations: string[];
    metadata: any;
}

export interface ConnectionTestResult {
    success: boolean;
    response_time: number;
    response: string;
    tokens_used: number;
    timestamp: string;
}

export function useRealtimeModels() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getCapabilities = useCallback(async () => {
        try {
            setLoading(true);
            const response = await apiClient.get(API_ENDPOINTS.realtimeModelIntegration.status); // Using status/capabilities endpoint
            if (response.success && response.data) return response.data;
            throw new Error(response.error || 'Failed to get capabilities');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to get capabilities');
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const getProviders = useCallback(async () => {
        try {
            const response: ApiResponse<{ providers: any[] }> = await apiClient.get(API_ENDPOINTS.realtimeModelIntegration.providers);
            return response; // full response with success flag and providers
        } catch (err) {
            console.error(err);
            return null;
        }
    }, []);

    const getBiasTestTypes = useCallback(async () => {
        try {
            const response: ApiResponse<{ test_types: any[] }> = await apiClient.get(API_ENDPOINTS.realtimeModelIntegration.biasTestTypes);
            return response; // full response with success flag and test types
        } catch (err) {
            console.error(err);
            return null;
        }
    }, []);

    const configureModel = useCallback(async (config: ModelConfig) => {
        try {
            setLoading(true);
            const response = await apiClient.post(API_ENDPOINTS.realtimeModelIntegration.configureModel, config);
            if (response.success && response.data) return response.data;
            throw new Error(response.error || 'Failed to configure model');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to configure model';
            setError(msg);
            throw new Error(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    const testConnection = useCallback(async (config: ModelConfig) => {
        try {
            setLoading(true);
            const response = await apiClient.post<ConnectionTestResult>(API_ENDPOINTS.realtimeModelIntegration.testConnection, {
                model_config: config
            });
            if (response.success && response.data) return response.data;
            throw new Error(response.error || 'Connection test failed');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Connection test failed';
            setError(msg);
            throw new Error(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    const performBiasTest = useCallback(async (
        config: ModelConfig,
        testType: string,
        testGroups: string[],
        customPrompt?: string
    ) => {
        try {
            setLoading(true);
            const response = await apiClient.post<BiasTestResult>(API_ENDPOINTS.realtimeModelIntegration.performBiasTest, {
                model_config: config,
                test_type: testType,
                test_groups: testGroups,
                custom_prompt: customPrompt
            });
            if (response.success && response.data) return response.data;
            throw new Error(response.error || 'Bias test failed');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Bias test failed';
            setError(msg);
            throw new Error(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    const performComprehensiveAnalysis = useCallback(async (
        config: ModelConfig,
        testGroups: string[],
        customTests?: any[]
    ) => {
        try {
            setLoading(true);
            const response = await apiClient.post<ComprehensiveAnalysisResult>(API_ENDPOINTS.realtimeModelIntegration.comprehensiveAnalysis, {
                model_config: config,
                test_groups: testGroups,
                custom_tests: customTests,
                include_all_tests: true
            });
            if (response.success && response.data) return response.data;
            throw new Error(response.error || 'Comprehensive analysis failed');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Comprehensive analysis failed';
            setError(msg);
            throw new Error(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        getProviders,
        getBiasTestTypes,
        configureModel,
        testConnection,
        performBiasTest,
        performComprehensiveAnalysis
    };
}
