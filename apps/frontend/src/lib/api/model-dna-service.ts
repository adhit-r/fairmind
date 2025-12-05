/**
 * Model DNA API Service
 * Handles all Model DNA and lineage-related API calls
 */

import { apiClient, type ApiResponse } from './api-client'

export interface ModelDNA {
    model_id: string
    dna_id: string
    architecture_genes: string
    data_genes: string
    training_genes: string
    bias_profile: {
        overall_bias_score: number
        detected_biases: string[]
        fairness_metrics: Record<string, number>
    }
    performance_fingerprint: Record<string, number>
    generation: number
    ancestors: string[]
    created_at: string
}

export interface ModelComparison {
    model_1: {
        id: string
        dna_id: string
    }
    model_2: {
        id: string
        dna_id: string
    }
    similarity_scores: {
        architecture: number
        data: number
        training: number
        bias_profile: number
        performance: number
        overall: number
    }
    common_ancestors: string[]
    divergence_points: string[]
    relationship: string
}

export interface LineageNode {
    id: string
    type: 'model' | 'dataset'
    name: string
    version?: string
    framework?: string
    depth: number
    bias_score?: number
    performance?: Record<string, number>
    source?: string
}

export interface LineageEdge {
    source: string
    target: string
    type: string
    label: string
}

export interface LineageTree {
    root_model_id: string
    nodes: LineageNode[]
    edges: LineageEdge[]
    total_nodes: number
    total_edges: number
    max_depth: number
}

export interface SimilarModel {
    model_id: string
    model_name: string
    similarity_score: number
    relationship: string
    dna_id: string
}

class ModelDNAService {
    /**
     * Get DNA fingerprint for a model
     */
    async getModelDNA(modelId: string): Promise<ApiResponse<{ dna: ModelDNA }>> {
        return apiClient.get<{ dna: ModelDNA }>(`/api/v1/provenance/dna/${modelId}`)
    }

    /**
     * Compare DNA of two models
     */
    async compareModels(modelId1: string, modelId2: string): Promise<ApiResponse<{ comparison: ModelComparison }>> {
        const formData = new FormData()
        formData.append('model_id1', modelId1)
        formData.append('model_id2', modelId2)

        return apiClient.post<{ comparison: ModelComparison }>('/api/v1/provenance/dna/compare', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        })
    }

    /**
     * Get lineage tree for a model
     */
    async getLineageTree(modelId: string): Promise<ApiResponse<{ lineage_tree: LineageTree }>> {
        return apiClient.get<{ lineage_tree: LineageTree }>(`/api/v1/provenance/lineage-tree/${modelId}`)
    }

    /**
     * Search for similar models
     */
    async searchSimilar(
        modelId: string,
        similarityThreshold: number = 0.7,
        maxResults: number = 10
    ): Promise<ApiResponse<{
        reference_model_id: string
        reference_dna_id: string
        similar_models: SimilarModel[]
        count: number
    }>> {
        return apiClient.get(
            `/api/v1/provenance/dna/search?model_id=${modelId}&similarity_threshold=${similarityThreshold}&max_results=${maxResults}`
        )
    }

    /**
     * List all models with provenance
     */
    async listModels(): Promise<ApiResponse<{ models: any[] }>> {
        return apiClient.get('/api/v1/provenance/models')
    }
}

export const modelDNAService = new ModelDNAService()
