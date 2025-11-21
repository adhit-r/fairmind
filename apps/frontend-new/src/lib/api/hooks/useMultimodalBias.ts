/**
 * Multimodal Bias Detection API Hooks
 */

import { useState, useCallback } from 'react'
import { apiClient, type ApiResponse } from '../api-client'

export interface MultimodalBiasResult {
  modality: 'image' | 'audio' | 'video' | 'cross-modal'
  biasType: string
  biasScore: number
  confidence: number
  isBiased: boolean
  details?: Record<string, any>
  recommendations?: string[]
  timestamp: string
}

export interface ImageBiasRequest {
  model_outputs: Array<{
    text?: string
    image_url?: string
    metadata?: Record<string, any>
    protected_attributes?: Record<string, any>
  }>
  analysis_config?: Record<string, any>
}

export interface AudioBiasRequest {
  model_outputs: Array<{
    text?: string
    audio_url?: string
    metadata?: Record<string, any>
    protected_attributes?: Record<string, any>
  }>
  analysis_config?: Record<string, any>
}

export interface VideoBiasRequest {
  model_outputs: Array<{
    text?: string
    video_url?: string
    metadata?: Record<string, any>
    protected_attributes?: Record<string, any>
  }>
  analysis_config?: Record<string, any>
}

export interface CrossModalBiasRequest {
  model_outputs: Array<{
    text?: string
    image_url?: string
    audio_url?: string
    video_url?: string
    metadata?: Record<string, any>
    protected_attributes?: Record<string, any>
  }>
  modalities: string[]
  analysis_config?: Record<string, any>
}

export function useMultimodalBias() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const detectImageBias = async (request: ImageBiasRequest) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<MultimodalBiasResult[]> = await apiClient.post(
        '/api/v1/multimodal-bias/image-detection',
        request,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 30000,
        }
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Image bias detection failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Image bias detection failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const detectAudioBias = async (request: AudioBiasRequest) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<MultimodalBiasResult[]> = await apiClient.post(
        '/api/v1/multimodal-bias/audio-detection',
        request,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 30000,
        }
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Audio bias detection failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Audio bias detection failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const detectVideoBias = async (request: VideoBiasRequest) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<MultimodalBiasResult[]> = await apiClient.post(
        '/api/v1/multimodal-bias/video-detection',
        request,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 30000,
        }
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Video bias detection failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Video bias detection failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const detectCrossModalBias = async (request: CrossModalBiasRequest) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<MultimodalBiasResult[]> = await apiClient.post(
        '/api/v1/multimodal-bias/cross-modal-detection',
        request,
        {
          enableRetry: true,
          maxRetries: 3,
          timeout: 30000,
        }
      )
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Cross-modal bias detection failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Cross-modal bias detection failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return {
    detectImageBias,
    detectAudioBias,
    detectVideoBias,
    detectCrossModalBias,
    loading,
    error,
  }
}

