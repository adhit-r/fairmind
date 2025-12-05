import { apiClient } from './api-client';

export interface TrendPoint {
    date: string;
    bias_score: number;
    fairness_threshold: number;
}

export interface ComparisonPoint {
    model_id: string;
    name: string;
    demographic_parity: number;
    equal_opportunity: number;
    disparate_impact: number;
    overall_fairness: number;
}

export interface HeatmapPoint {
    attribute: string;
    metric: string;
    value: number;
    status: 'pass' | 'fail';
}

export const analyticsService = {
    getTrends: async (modelId: string, days: number = 30) => {
        const response = await apiClient.get(`/api/v1/analytics/trends/${modelId}?days=${days}`);
        return response;
    },

    compareModels: async (modelIds: string[]) => {
        const queryString = modelIds.map(id => `model_ids=${id}`).join('&');
        const response = await apiClient.get(`/api/v1/analytics/compare?${queryString}`);
        return response;
    },

    getHeatmap: async (modelId: string) => {
        const response = await apiClient.get(`/api/v1/analytics/heatmap/${modelId}`);
        return response;
    }
};
