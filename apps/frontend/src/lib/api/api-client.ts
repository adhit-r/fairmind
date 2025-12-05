/**
 * API Client - Base client for all API calls
 * Handles authentication, error handling, retry logic, and request/response interceptors
 */

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface ApiError {
  message: string
  status: number
  type: 'network' | 'server' | 'client' | 'timeout' | 'cors' | 'unknown'
  canRetry: boolean
}

enum ApiErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  CORS_ERROR = 'CORS_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  SERVER_ERROR = 'SERVER_ERROR',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN',
}

// Simple in-memory cache
const apiCache = new Map<string, { data: any; timestamp: number; ttl: number }>()

const getCachedData = (key: string): any | null => {
  const cached = apiCache.get(key)
  if (cached && Date.now() - cached.timestamp < cached.ttl) {
    return cached.data
  }
  if (cached) {
    apiCache.delete(key)
  }
  return null
}

const setCachedData = (key: string, data: any, ttl: number = 5 * 60 * 1000) => {
  apiCache.set(key, { data, timestamp: Date.now(), ttl })
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const classifyError = (error: any, response?: Response): ApiError => {
  if (typeof navigator !== 'undefined' && !navigator.onLine) {
    return {
      message: 'No internet connection. Please check your network.',
      status: 0,
      type: 'network',
      canRetry: true,
    }
  }

  if (response) {
    if (response.status === 404) {
      return {
        message: 'Endpoint not found',
        status: 404,
        type: 'client',
        canRetry: false,
      }
    }

    if (response.status >= 500) {
      return {
        message: 'Server error occurred',
        status: response.status,
        type: 'server',
        canRetry: true,
      }
    }

    if (response.status === 0 || error?.message?.includes('CORS')) {
      return {
        message: 'Connection blocked. Check CORS configuration.',
        status: 0,
        type: 'cors',
        canRetry: false,
      }
    }
  }

  if (error?.name === 'AbortError' || error?.message?.includes('timeout')) {
    return {
      message: 'Request timed out',
      status: 0,
      type: 'timeout',
      canRetry: true,
    }
  }

  return {
    message: error?.message || 'Unknown error occurred',
    status: 0,
    type: 'unknown',
    canRetry: true,
  }
}

interface RequestOptions extends RequestInit {
  enableRetry?: boolean
  maxRetries?: number
  retryDelay?: number
  timeout?: number
  cacheKey?: string
  useCache?: boolean
}

class ApiClient {
  private baseUrl: string
  private accessToken: string | null = null

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  setAccessToken(token: string | null) {
    this.accessToken = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    // Don't make requests during SSR
    if (typeof window === 'undefined') {
      return {
        success: false,
        error: 'API calls can only be made on the client side',
      }
    }

    const {
      enableRetry = true,
      maxRetries = 3,
      retryDelay = 1000,
      timeout = 10000,
      cacheKey,
      useCache = false,
      ...fetchOptions
    } = options

    // Check cache first
    if (useCache && cacheKey) {
      const cached = getCachedData(cacheKey)
      if (cached) {
        return {
          success: true,
          data: cached as T,
        }
      }
    }

    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(fetchOptions.headers as Record<string, string>),
    }

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`
    }

    let retryCount = 0
    const makeRequest = async (): Promise<ApiResponse<T>> => {
      try {
        // Create abort controller for timeout
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), timeout)

        const response = await fetch(url, {
          ...fetchOptions,
          headers,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const apiError = classifyError(null, response)

          // Retry logic for retryable errors
          if (enableRetry && apiError.canRetry && retryCount < maxRetries) {
            retryCount++
            const delay = retryDelay * Math.pow(2, retryCount - 1) // Exponential backoff
            await sleep(delay)
            return makeRequest()
          }

          const errorData = await response.json().catch(() => ({}))
          return {
            success: false,
            error: errorData.detail || errorData.error || errorData.message || apiError.message || `HTTP ${response.status}: ${response.statusText}`,
          } as ApiResponse<T>
        }

        const jsonData = await response.json()

        // Cache successful response
        if (useCache && cacheKey) {
          setCachedData(cacheKey, jsonData)
        }

        // Handle different response formats
        if (jsonData.success !== undefined) {
          // Already in ApiResponse format
          return jsonData as ApiResponse<T>
        } else {
          // Backend returns data directly, wrap it
          return {
            success: true,
            data: jsonData as T,
          }
        }
      } catch (error) {
        const apiError = classifyError(error)

        // Retry logic for retryable errors
        if (enableRetry && apiError.canRetry && retryCount < maxRetries) {
          retryCount++
          const delay = retryDelay * Math.pow(2, retryCount - 1) // Exponential backoff
          await sleep(delay)
          return makeRequest()
        }

        // Return error response instead of throwing
        if (error instanceof Error) {
          // Check if it's an abort error (timeout)
          if (error.name === 'AbortError') {
            return {
              success: false,
              error: 'Request timeout - please check your connection',
            } as ApiResponse<T>
          }
          return {
            success: false,
            error: apiError.message || error.message || 'Network error occurred',
          } as ApiResponse<T>
        }
        return {
          success: false,
          error: apiError.message || 'Unknown error occurred',
        } as ApiResponse<T>
      }
    }

    return makeRequest()
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    const isFormData = data instanceof FormData
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: isFormData ? data : (data ? JSON.stringify(data) : undefined),
      headers: {
        ...options?.headers,
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      }
    })
  }

  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }

  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }
}

export const apiClient = new ApiClient()

