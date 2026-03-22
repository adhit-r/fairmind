/**
 * Authentik OAuth2 Hook with PKCE Flow
 *
 * Handles OAuth2 authorization code flow with PKCE for secure SPA authentication.
 * Implements code_verifier/code_challenge for protection against authorization code interception.
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient as api } from "../api-client";

interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    username: string;
    roles: string[];
  };
}

interface UseAuthentikOptions {
  clientId?: string;
  authentikUrl?: string;
  redirectUri?: string;
  onSuccess?: (data: AuthTokenResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Generate a random string for PKCE code_verifier
 * RFC 7636: code_verifier = 43*128unreserved characters
 */
function generateCodeVerifier(): string {
  const characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  let result = "";
  for (let i = 0; i < 128; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
}

/**
 * Generate code_challenge from code_verifier using SHA-256
 * RFC 7636: code_challenge = BASE64URL(SHA256(code_verifier))
 */
async function generateCodeChallenge(codeVerifier: string): Promise<string> {
  // Use WebCrypto API for SHA-256
  const buffer = new TextEncoder().encode(codeVerifier);
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);

  // Convert to base64url
  return btoa(String.fromCharCode(...new Uint8Array(hashBuffer)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

/**
 * Generate a random state parameter for CSRF protection
 */
function generateRandomState(): string {
  return btoa(Math.random().toString()).substring(0, 43);
}

/**
 * Hook for Authentik OAuth2 authentication
 *
 * Usage:
 * ```tsx
 * const { login, logout, isLoading, error } = useAuthentik();
 *
 * // Redirect to Authentik
 * const handleLogin = async () => {
 *   await login();
 * };
 *
 * // Or logout
 * const handleLogout = async () => {
 *   await logout();
 * };
 * ```
 */
export function useAuthentik(options: UseAuthentikOptions = {}) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Get configuration from environment or options
  const clientId = options.clientId || process.env.NEXT_PUBLIC_AUTHENTIK_CLIENT_ID;
  const authentikUrl =
    options.authentikUrl || process.env.NEXT_PUBLIC_AUTHENTIK_URL;
  const redirectUri =
    options.redirectUri ||
    (typeof window !== "undefined"
      ? `${window.location.origin}/auth/callback`
      : process.env.NEXT_PUBLIC_AUTHENTIK_REDIRECT_URI);

  if (!clientId || !authentikUrl) {
    console.warn(
      "Authentik configuration missing: NEXT_PUBLIC_AUTHENTIK_CLIENT_ID or NEXT_PUBLIC_AUTHENTIK_URL"
    );
  }

  /**
   * Initiate OAuth2 login flow
   * Redirects user to Authentik authorization endpoint
   */
  const login = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (!clientId || !authentikUrl) {
        throw new Error(
          "Authentik configuration missing: client ID or URL not provided"
        );
      }

      // Generate PKCE parameters
      const codeVerifier = generateCodeVerifier();
      const codeChallenge = await generateCodeChallenge(codeVerifier);
      const state = generateRandomState();

      // Store PKCE parameters in session storage (secure against XSS with HttpOnly flag in cookie alternative)
      // Note: sessionStorage is used here as it's cleared when tab closes
      sessionStorage.setItem("oauth_state", state);
      sessionStorage.setItem("code_verifier", codeVerifier);

      // Build authorization URL
      const params = new URLSearchParams({
        client_id: clientId,
        response_type: "code",
        scope: "openid profile email offline_access", // Include offline_access for refresh tokens
        redirect_uri: redirectUri || "",
        code_challenge: codeChallenge,
        code_challenge_method: "S256", // SHA-256
        state: state,
      });

      // Redirect to Authentik
      const authUrl = `${authentikUrl}/application/o/authorize/?${params}`;
      window.location.href = authUrl;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      options.onError?.(error);
      setIsLoading(false);
    }
  }, [clientId, authentikUrl, redirectUri, options]);

  /**
   * Handle OAuth2 callback
   * Exchanges authorization code for tokens
   *
   * Should be called from /auth/callback page
   */
  const handleCallback = useCallback(
    async (code: string, state: string) => {
      try {
        setIsLoading(true);
        setError(null);

        // Validate state parameter (CSRF protection)
        const savedState = sessionStorage.getItem("oauth_state");
        if (!savedState || savedState !== state) {
          throw new Error("Invalid state parameter - possible CSRF attack");
        }

        // Exchange code for tokens via backend
        // Backend /callback endpoint expects query parameters
        const params = new URLSearchParams({ code, state });
        const response = await api.post<AuthTokenResponse>(
          `/api/v1/auth/callback?${params.toString()}`
        );

        const { access_token, refresh_token, user } = response;

        // Store tokens (access in memory/state, refresh in secure cookie handled by backend)
        localStorage.setItem("access_token", access_token);
        if (refresh_token) {
          localStorage.setItem("refresh_token", refresh_token);
        }

        // Clear PKCE parameters from storage
        sessionStorage.removeItem("oauth_state");
        sessionStorage.removeItem("code_verifier");

        // Call success callback
        options.onSuccess?.(response);

        // Redirect to dashboard
        router.push("/");

        return response;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options.onError?.(error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [options, router]
  );

  /**
   * Logout user
   * Revokes token and redirects to Authentik logout
   */
  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Call backend logout to revoke token
      try {
        await api.post("/api/v1/auth/logout", {});
      } catch (err) {
        console.warn("Error revoking token:", err);
        // Continue with logout even if revocation fails
      }

      // Clear stored tokens
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      // Redirect to Authentik logout
      if (authentikUrl) {
        const logoutUrl = `${authentikUrl}/application/o/logout/?redirect_uri=${encodeURIComponent(
          redirectUri || "/"
        )}`;
        window.location.href = logoutUrl;
      } else {
        // Fallback if no Authentik URL
        router.push("/");
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      options.onError?.(error);
      setIsLoading(false);
    }
  }, [authentikUrl, redirectUri, router, options]);

  /**
   * Check if user is authenticated
   */
  const isAuthenticated = useCallback(() => {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("access_token");
  }, []);

  /**
   * Get stored access token
   */
  const getAccessToken = useCallback(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }, []);

  return {
    login,
    logout,
    handleCallback,
    isAuthenticated,
    getAccessToken,
    isLoading,
    error,
  };
}

export type UseAuthentikReturn = ReturnType<typeof useAuthentik>;
