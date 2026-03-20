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
        apiClient.setRefreshToken(response.data.refresh_token)
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

  const register = async (data: any) => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<User> = await apiClient.post(
        API_ENDPOINTS.auth.register,
        data
      )

      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.error || 'Registration failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Registration failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await apiClient.post(API_ENDPOINTS.auth.logout)
      apiClient.clearSession()
      setUser(null)
    } catch (err) {
      console.error('Logout error:', err)
      apiClient.clearSession()
      setUser(null)
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
      throw new Error(response.error || 'Failed to get current user')
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to get user')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return {
    user,
    loading,
    error,
    login,
    register,
    logout,
    getCurrentUser,
  }
}
