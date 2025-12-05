/**
 * Remediation API Service
 * Handles all remediation wizard API calls
 */

import { apiClient, type ApiResponse } from './api-client'

export interface BiasMetrics {
    statistical_parity_difference: number
    equalized_odds_tpr_difference?: number
    equalized_odds_fpr_difference?: number
    equal_opportunity_difference?: number
    [key: string]: number | undefined
}

export interface RemediationStep {
    step_id: number
    title: string
    description: string
    strategy: string
    estimated_improvement: number
    estimated_time_minutes: number
    difficulty: 'easy' | 'medium' | 'hard'
    selected?: boolean
}

export interface RemediationPlan {
    plan_id: string
    created_at: string
    recommended_steps: RemediationStep[]
    estimated_total_improvement: number
    estimated_total_time_minutes: number
    priority_score: number
}

export interface AnalyzeRequest {
    test_id?: string
    model_id?: string
    dataset_id?: string
    predictions?: number[]
    ground_truth?: number[]
    sensitive_attributes: Record<string, any[]>
    bias_metrics: BiasMetrics
}

export interface GeneratePipelineRequest {
    plan_id: string
    selected_step_ids: number[]
}

export interface GeneratedPipeline {
    plan_id: string
    selected_steps: number[]
    code: string
    language: string
}

class RemediationService {
    /**
     * Analyze bias and get remediation recommendations
     */
    async analyzeAndRecommend(request: AnalyzeRequest): Promise<ApiResponse<{ plan: RemediationPlan }>> {
        return apiClient.post<{ plan: RemediationPlan }>('/api/v1/remediation/analyze', request)
    }

    /**
     * Get all available remediation strategies
     */
    async getStrategies(): Promise<ApiResponse<{ strategies: any[]; count: number }>> {
        return apiClient.get('/api/v1/remediation/strategies', {
            useCache: true,
            cacheKey: 'remediation-strategies',
        })
    }

    /**
     * Apply a single remediation step
     */
    async applyStep(stepId: number, dataset?: any): Promise<ApiResponse<any>> {
        return apiClient.post('/api/v1/remediation/apply-step', {
            step_id: stepId,
            dataset,
        })
    }

    /**
     * Generate complete remediation pipeline code
     */
    async generatePipeline(request: GeneratePipelineRequest): Promise<ApiResponse<GeneratedPipeline>> {
        return apiClient.post<GeneratedPipeline>('/api/v1/remediation/generate-pipeline', request)
    }

    /**
     * Health check for remediation service
     */
    async healthCheck(): Promise<ApiResponse<any>> {
        return apiClient.get('/api/v1/remediation/health')
    }
}

export const remediationService = new RemediationService()
