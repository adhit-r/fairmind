/**
 * OAuth2 PKCE Utilities
 *
 * Implements RFC 7636 PKCE (Proof Key for Public Clients) for secure OAuth2 authorization code flow
 * in Single-Page Applications (SPAs).
 */

/**
 * Generate a random code_verifier for PKCE
 * RFC 7636 specifies: code_verifier = 43*128 unreserved characters
 * Unreserved characters: [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
 *
 * @returns A random 128-character code verifier
 */
export function generateCodeVerifier(): string {
  return randomString(128, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~')
}

/**
 * A random string drawn from `alphabet` with the Web Crypto CSPRNG.
 * Rejection sampling keeps every character equally likely.
 */
export function randomString(length: number, alphabet: string): string {
  const limit = 256 - (256 % alphabet.length)
  let result = ''
  while (result.length < length) {
    for (const byte of crypto.getRandomValues(new Uint8Array(length))) {
      if (byte < limit && result.length < length) result += alphabet[byte % alphabet.length]
    }
  }
  return result
}

/**
 * Generate code_challenge from code_verifier using SHA-256
 * RFC 7636: code_challenge = BASE64URL(SHA256(code_verifier))
 *
 * @param codeVerifier The code verifier string
 * @returns Base64URL-encoded SHA-256 hash of code verifier
 */
export async function generateCodeChallenge(codeVerifier: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(codeVerifier)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  return arrayBufferToBase64url(hashBuffer)
}

/**
 * Generate a random state parameter for CSRF protection
 * Used to prevent authorization code interception attacks
 *
 * @returns A random state string
 */
export function generateState(): string {
  return randomString(32, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
}

/**
 * Convert ArrayBuffer to Base64URL encoding
 * Used for encoding SHA-256 hashes for OAuth2 code_challenge
 *
 * @param buffer ArrayBuffer to encode
 * @returns Base64URL-encoded string
 */
function arrayBufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

/**
 * Store PKCE parameters in sessionStorage
 * sessionStorage is used as it's cleared when the tab closes
 *
 * @param state CSRF token
 * @param codeVerifier Code verifier for token exchange
 */
export function storePKCEParameters(state: string, codeVerifier: string): void {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('oauth_state', state)
    sessionStorage.setItem('code_verifier', codeVerifier)
  }
}

/**
 * Retrieve PKCE parameters from sessionStorage
 *
 * @returns Object with state and codeVerifier, or null if not found
 */
export function retrievePKCEParameters(): { state: string; codeVerifier: string } | null {
  if (typeof window === 'undefined') return null

  const state = sessionStorage.getItem('oauth_state')
  const codeVerifier = sessionStorage.getItem('code_verifier')

  if (!state || !codeVerifier) {
    return null
  }

  return { state, codeVerifier }
}

/**
 * Clear PKCE parameters from sessionStorage
 * Called after successful token exchange to clean up sensitive data
 */
export function clearPKCEParameters(): void {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem('oauth_state')
    sessionStorage.removeItem('code_verifier')
  }
}

/**
 * Validate PKCE state parameter
 * Ensures the state returned from OAuth2 provider matches what was sent
 * This protects against CSRF attacks
 *
 * @param returnedState State parameter returned from OAuth2 provider
 * @returns true if state is valid, false otherwise
 */
export function validateState(returnedState: string): boolean {
  if (typeof window === 'undefined') return false

  const savedState = sessionStorage.getItem('oauth_state')
  if (!savedState || savedState !== returnedState) {
    return false
  }

  return true
}
