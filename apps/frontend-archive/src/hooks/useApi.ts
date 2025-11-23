import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

interface UseApiOptions {
  enableRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  fallbackData?: any;
  cacheKey?: string;
  refreshInterval?: number;
  timeout?: number;
}

enum ApiErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  CORS_ERROR = 'CORS_ERROR', 
  NOT_FOUND = 'NOT_FOUND',
  SERVER_ERROR = 'SERVER_ERROR',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}

interface ApiError {
  type: ApiErrorType;
  message: string;
  status?: number;
  canRetry: boolean;
}

// Simple in-memory cache
const apiCache = new Map<string, { data: any; timestamp: number; ttl: number }>();

// Cache utilities
const getCachedData = (key: string): any | null => {
  const cached = apiCache.get(key);
  if (cached && Date.now() - cached.timestamp < cached.ttl) {
    return cached.data;
  }
  if (cached) {
    apiCache.delete(key); // Remove expired cache
  }
  return null;
};

const setCachedData = (key: string, data: any, ttl: number = 5 * 60 * 1000) => {
  apiCache.set(key, { data, timestamp: Date.now(), ttl });
};

// Error classification
const classifyError = (error: any, response?: Response): ApiError => {
  if (!navigator.onLine) {
    return {
      type: ApiErrorType.NETWORK_ERROR,
      message: 'No internet connection. Please check your network.',
      canRetry: true
    };
  }

  if (response) {
    if (response.status === 404) {
      return {
        type: ApiErrorType.NOT_FOUND,
        message: 'Endpoint not found. Using fallback data.',
        status: 404,
        canRetry: false
      };
    }
    
    if (response.status >= 500) {
      return {
        type: ApiErrorType.SERVER_ERROR,
        message: 'Server error. Retrying...',
        status: response.status,
        canRetry: true
      };
    }
    
    if (response.status === 0 || error.message?.includes('CORS')) {
      return {
        type: ApiErrorType.CORS_ERROR,
        message: 'Connection blocked. Check CORS configuration.',
        canRetry: false
      };
    }
  }

  if (error.name === 'AbortError' || error.message?.includes('timeout')) {
    return {
      type: ApiErrorType.TIMEOUT,
      message: 'Request timed out. Retrying...',
      canRetry: true
    };
  }

  return {
    type: ApiErrorType.UNKNOWN,
    message: error.message || 'Unknown error occurred',
    canRetry: true
  };
};

// Retry with exponential backoff
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export function useApi<T>(endpoint: string, options: UseApiOptions = {}) {
  const {
    enableRetry = true,
    maxRetries = 3,
    retryDelay = 1000,
    fallbackData,
    cacheKey,
    refreshInterval,
    timeout = 10000
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async (isRetry = false) => {
    // Check cache first
    const effectiveCacheKey = cacheKey || endpoint;
    if (!isRetry) {
      const cachedData = getCachedData(effectiveCacheKey);
      if (cachedData) {
        setData(cachedData);
        setLoading(false);
        setError(null);
        return;
      }
    }

    // Skip fetch if endpoint is empty
    if (!endpoint || endpoint.trim() === '') {
      if (fallbackData) {
        setData(fallbackData);
      }
      setLoading(false);
      setError(null);
      return;
    }

    try {
      if (!isRetry) {
        setLoading(true);
        setError(null);
      }

      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();
      
      // Set up timeout
      const timeoutId = setTimeout(() => {
        abortControllerRef.current?.abort();
      }, timeout);

      const response = await fetch(`${API_BASE}${endpoint}`, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const apiError = classifyError(null, response);
        
        // Handle specific error types
        if (apiError.type === ApiErrorType.NOT_FOUND && fallbackData) {
          setData(fallbackData);
          setError(null);
          return;
        }
        
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result: ApiResponse<T> = await response.json();

      if (result.success && result.data !== undefined) {
        setData(result.data);
        setError(null);
        setRetryCount(0);
        
        // Cache successful response
        setCachedData(effectiveCacheKey, result.data);
      } else {
        throw new Error(result.error || 'API call failed');
      }
    } catch (err: any) {
      const apiError = classifyError(err);
      
      // Handle fallback data for certain error types
      if ((apiError.type === ApiErrorType.NOT_FOUND || 
           apiError.type === ApiErrorType.CORS_ERROR) && fallbackData) {
        setData(fallbackData);
        setError(null);
        return;
      }

      // Retry logic
      if (enableRetry && apiError.canRetry && retryCount < maxRetries) {
        const delay = retryDelay * Math.pow(2, retryCount); // Exponential backoff
        setRetryCount(prev => prev + 1);
        
        await sleep(delay);
        return fetchData(true);
      }

      setError(apiError);
      setData(fallbackData || null);
    } finally {
      setLoading(false);
    }
  }, [endpoint, enableRetry, maxRetries, retryDelay, fallbackData, cacheKey, timeout, retryCount]);

  const retry = useCallback(() => {
    setRetryCount(0);
    fetchData();
  }, [fetchData]);

  const refresh = useCallback(() => {
    // Clear cache and fetch fresh data
    const effectiveCacheKey = cacheKey || endpoint;
    apiCache.delete(effectiveCacheKey);
    setRetryCount(0);
    fetchData();
  }, [fetchData, cacheKey, endpoint]);

  useEffect(() => {
    fetchData();

    // Set up refresh interval if specified
    if (refreshInterval && refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        fetchData();
      }, refreshInterval);
    }

    // Cleanup function
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { 
    data, 
    loading, 
    error, 
    retry, 
    refresh,
    retryCount 
  };
}

export function useApiCall() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const call = async <T>(
    endpoint: string, 
    options?: RequestInit & { 
      enableRetry?: boolean;
      maxRetries?: number;
      timeout?: number;
    }
  ): Promise<T | null> => {
    const {
      enableRetry = true,
      maxRetries = 3,
      timeout = 10000,
      ...fetchOptions
    } = options || {};

    let retryCount = 0;

    const makeRequest = async (): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);

        const abortController = new AbortController();
        const timeoutId = setTimeout(() => {
          abortController.abort();
        }, timeout);

        const response = await fetch(`${API_BASE}${endpoint}`, {
          headers: {
            'Content-Type': 'application/json',
            ...fetchOptions?.headers,
          },
          signal: abortController.signal,
          ...fetchOptions,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const apiError = classifyError(null, response);
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result: ApiResponse<T> = await response.json();

        if (result.success && result.data !== undefined) {
          return result.data;
        } else {
          throw new Error(result.error || 'API call failed');
        }
      } catch (err: any) {
        const apiError = classifyError(err);

        // Retry logic for retryable errors
        if (enableRetry && apiError.canRetry && retryCount < maxRetries) {
          retryCount++;
          const delay = 1000 * Math.pow(2, retryCount - 1); // Exponential backoff
          await sleep(delay);
          return makeRequest();
        }

        setError(apiError);
        throw err;
      } finally {
        setLoading(false);
      }
    };

    try {
      return await makeRequest();
    } catch (err) {
      return null;
    }
  };

  return { call, loading, error };
}