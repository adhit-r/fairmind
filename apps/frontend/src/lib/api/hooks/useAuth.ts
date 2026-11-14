/**
 * Authentication API Hooks
 *
 * Supports both JWT-based login (legacy) and OAuth2/Authentik flow (new RBAC).
 * Maintains backward compatibility while enabling OAuth2 transitions.
 */

import { useState } from 'react'
import { apiClient, DEMO_FLAG, type ApiResponse } from '../api-client'
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

  const login = (credentials: LoginRequest, headers?: Record<string, string>) =>
    signIn(API_ENDPOINTS.auth.login, credentials, headers)

  /** Signs in to the public demo organisation, read-only. */
  const loginDemo = async (headers?: Record<string, string>) => {
    const data = await signIn(API_ENDPOINTS.auth.demo, {}, headers)
    localStorage.setItem(DEMO_FLAG, '1')
    return data
  }

  const signIn = async (path: string, body: unknown, headers?: Record<string, string>) => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<LoginResponse> = await apiClient.post(path, body, { headers })

      if (response.success && response.data) {
        apiClient.setAccessToken(response.data.access_token)
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', response.data.access_token)
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

  const register = async (data: {
    name: string
    email: string
    password: string
    invitation_token: string
  }, headers?: Record<string, string>) => {
    try {
      setLoading(true)
      setError(null)

      const response: ApiResponse<LoginResponse> = await apiClient.post(
        API_ENDPOINTS.auth.register,
        data,
        { headers }
      )

      if (response.success && response.data) {
        apiClient.setAccessToken(response.data.access_token)
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', response.data.access_token)
        }
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
        const { access_token, user } = response.data

        // Store tokens
        apiClient.setAccessToken(access_token)
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access_token)
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

  return {
    user,
    loading,
    error,
    login,
    loginDemo,
    register,
    logout,
    handleAuthenticCallback,
  }
}
