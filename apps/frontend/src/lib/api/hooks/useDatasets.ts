import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export interface Dataset {
  id: string
  name: string
  description?: string
  file_type: string
  row_count?: number
  column_count?: number
  created_at: string
  schema_json?: Record<string, any>
  protected_attributes?: string[]
  target_variable?: string
}

export interface DatasetListResponse {
  success: boolean
  datasets: Dataset[]
  total: number
  page: number
  limit: number
}

export interface DatasetUploadResponse {
  success: boolean
  dataset: Dataset
  message?: string
  error?: string
}

export function useDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  const fetchDatasets = useCallback(async (page = 1, limit = 100, search?: string) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      })
      if (search) {
        params.append('search', search)
      }

      const response = await apiClient.get<DatasetListResponse>(
        `${API_ENDPOINTS.datasets.list}?${params.toString()}`,
        {
          maxRetries: 2,
          timeout: 10000,
        }
      )

      if (response.success) {
        const data = response as any
        setDatasets(data.datasets || data.data?.datasets || [])
        setTotal(data.total || data.data?.total || 0)
      } else {
        setError('Failed to fetch datasets')
        setDatasets([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch datasets')
      setDatasets([])
    } finally {
      setLoading(false)
    }
  }, [])

  const uploadDataset = useCallback(async (
    file: File,
    name?: string,
    description?: string
  ): Promise<DatasetUploadResponse> => {
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (name) formData.append('name', name)
      if (description) formData.append('description', description)

      const response = await apiClient.post<DatasetUploadResponse>(
        API_ENDPOINTS.datasets.upload,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      if (response.success) {
        // Refresh dataset list
        await fetchDatasets()
        return response as unknown as DatasetUploadResponse
      } else {
        throw new Error(response.error || 'Upload failed')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload dataset'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchDatasets])

  useEffect(() => {
    fetchDatasets()
  }, [fetchDatasets])

  return {
    datasets,
    loading,
    error,
    total,
    fetchDatasets,
    uploadDataset,
    refetch: () => fetchDatasets(),
  }
}
