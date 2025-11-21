/**
 * Authentication API Hooks
 */

import { useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { LoginRequest, LoginResponse, User } from '../types'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const login = async (credentials: LoginRequest) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: ApiResponse<LoginResponse> = await apiClient.post(
        API_ENDPOINTS.auth.login,
        credentials
      )
      
      if (response.success && response.data) {
        apiClient.setAccessToken(response.data.access_token)
        // Store token in localStorage or secure storage
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)
        }
        return response.data
      } else {
        throw new Error(response.error || 'Login failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Login failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await apiClient.post(API_ENDPOINTS.auth.logout)
      apiClient.setAccessToken(null)
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
      setUser(null)
    } catch (err) {
      console.error('Logout error:', err)
    }
  }

  const getCurrentUser = async () => {
    try {
      setLoading(true)
      const response: ApiResponse<User> = await apiClient.get(API_ENDPOINTS.auth.me)
      
      if (response.success && response.data) {
        setUser(response.data)
        return response.data
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to get user'))
    } finally {
      setLoading(false)
    }
  }

  return {
    user,
    loading,
    error,
    login,
    logout,
    getCurrentUser,
  }
}

