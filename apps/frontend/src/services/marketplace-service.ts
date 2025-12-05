import { apiClient } from '@/lib/api/api-client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

export interface ModelTag {
    name: string;
    category: string;
}

export interface ModelReview {
    review_id: string;
    model_id: string;
    user_id: string;
    rating: number;
    comment: string;
    created_at: string;
}

export interface MarketplaceModel {
    model_id: string;
    name: string;
    description: string;
    author: string;
    version: string;
    framework: string;
    task: string;
    tags: ModelTag[];
    bias_card: {
        overall_score: number;
        metrics: Record<string, number>;
    };
    performance_metrics: Record<string, number>;
    reviews: ModelReview[];
    download_count: number;
    created_at: string;
    updated_at: string;
}

export interface ListModelsResponse {
    success: boolean;
    models: MarketplaceModel[];
    count: number;
}

export interface GetModelResponse {
    success: boolean;
    model: MarketplaceModel;
}

export const marketplaceService = {
    async listModels(params?: {
        q?: string;
        framework?: string;
        task?: string;
        min_rating?: number;
    }): Promise<ListModelsResponse> {
        const queryParams = new URLSearchParams();
        if (params?.q) queryParams.append('q', params.q);
        if (params?.framework) queryParams.append('framework', params.framework);
        if (params?.task) queryParams.append('task', params.task);
        if (params?.min_rating) queryParams.append('min_rating', params.min_rating.toString());

        const response = await apiClient.get<ListModelsResponse>(`${API_ENDPOINTS.marketplace.models}?${queryParams.toString()}`);
        return response.data!;
    },

    async getModel(modelId: string): Promise<GetModelResponse> {
        const response = await apiClient.get<GetModelResponse>(API_ENDPOINTS.marketplace.model(modelId));
        return response.data!;
    },

    async publishModel(data: Omit<MarketplaceModel, 'model_id' | 'created_at' | 'updated_at' | 'reviews' | 'download_count'>): Promise<GetModelResponse> {
        const response = await apiClient.post<GetModelResponse>(API_ENDPOINTS.marketplace.publish, data);
        return response.data!;
    },

    async addReview(modelId: string, data: { user_id: string; rating: number; comment: string }): Promise<{ success: boolean; review: ModelReview }> {
        const response = await apiClient.post<{ success: boolean; review: ModelReview }>(API_ENDPOINTS.marketplace.reviews(modelId), data);
        return response.data!;
    }
};
