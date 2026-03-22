/**
 * Authentication API Hooks
 *
 * Supports both JWT-based login (legacy) and OAuth2/Authentik flow (new RBAC).
 * Maintains backward compatibility while enabling OAuth2 transitions.
 */

import { useState } from 'react'
import { apiClient, type ApiResponse } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import type { LoginRequest, LoginResponse, User } from '../types'

/**
 * OAuth2 Token Response from Backend
 * Returned after code exchange with Authentik
 */
export interface OAuth2TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: User
}

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

  /**
   * Logout user
   * Clears tokens and session
   */
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

  /**
   * Initiate OAuth2 login flow with Authentik
   * Redirects to Authentik authorization endpoint using PKCE flow
   */
  const loginWithAuthentik = async () => {
    try {
      setLoading(true)
      setError(null)

      const { useAuthentik } = await import('./useAuthentik')
      const { login } = useAuthentik()
      await login()
    } catch (err) {
      const error = err instanceof Error ? err : new Error('OAuth2 login failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle OAuth2 callback after Authentik redirect
   * Exchanges authorization code for tokens
   *
   * Called from /auth/callback page
   * Validates PKCE state parameter and exchanges code for tokens via backend
   */
  const handleAuthenticCallback = async (code: string, state: string) => {
    try {
      setLoading(true)
      setError(null)

      // Exchange code for tokens via backend OAuth2 endpoint
      // Backend will handle PKCE code_verifier validation and token exchange with Authentik
      const response: ApiResponse<OAuth2TokenResponse> = await apiClient.post(
        '/api/v1/auth/callback',
        { code, state }
      )

      if (response.success && response.data) {
        const { access_token, refresh_token, user } = response.data

        // Store tokens
        apiClient.setAccessToken(access_token)
        if (refresh_token) {
          apiClient.setRefreshToken(refresh_token)
        }
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access_token)
          if (refresh_token) {
            localStorage.setItem('refresh_token', refresh_token)
          }
        }

        // Set user in state
        setUser(user)

        return response.data
      } else {
        throw new Error(response.error || 'OAuth2 callback failed')
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('OAuth2 callback handling failed')
      setError(error)
      throw error
    } finally {
      setLoading(false)
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
    loginWithAuthentik,
    handleAuthenticCallback,
    getCurrentUser,
  }
}
