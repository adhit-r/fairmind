'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useOrg } from '@/context/OrgContext'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { OrangeLogo } from '@/components/OrangeLogo'
import { IconAlertTriangle, IconCheck } from '@tabler/icons-react'

/**
 * Invitation Details returned from backend
 */
interface InvitationDetails {
  org_id: string
  org_name: string
  email: string
  role: string
  created_at: string
  expires_at: string
}

/**
 * Acceptance Response from backend
 */
interface AcceptanceResponse {
  message: string
  org_id: string
  org_name: string
}

/**
 * State for the invitation page
 */
type PageState = 'loading' | 'ready' | 'accepting' | 'success' | 'error'

/**
 * Error types for user-friendly messages
 */
interface ErrorDetails {
  type: 'invalid' | 'expired' | 'email_mismatch' | 'already_member' | 'unknown'
  message: string
}

/**
 * Org Invitation Acceptance Page
 *
 * Allows users to accept organization invitations.
 * Flow:
 * 1. Extract token from URL
 * 2. Fetch invitation details to verify it's valid
 * 3. Display org name, role, and email
 * 4. On accept: POST to /invitations/{token}/accept
 * 5. Show success message with countdown to redirect
 *
 * Handles:
 * - Unauthenticated users (redirect to login)
 * - Invalid/expired tokens (400)
 * - Email mismatch (403)
 * - Already a member (409)
 */
export default function InvitationPage() {
  const params = useParams()
  const router = useRouter()
  const token = params?.token as string

  const { organizations, refreshOrgs } = useOrg()

  const [state, setState] = useState<PageState>('loading')
  const [error, setError] = useState<ErrorDetails | null>(null)
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null)
  const [countdown, setCountdown] = useState(2)
  const [userEmail, setUserEmail] = useState<string>('')

  /**
   * Fetch invitation details on mount
   */
  useEffect(() => {
    const fetchInvitation = async () => {
      if (!token) {
        setError({
          type: 'invalid',
          message: 'No invitation token provided. This link may be incomplete.',
        })
        setState('error')
        return
      }

      try {
        setState('loading')
        const response: ApiResponse<InvitationDetails> = await apiClient.get(
          API_ENDPOINTS.invitations.getDetails(token),
          { enableRetry: false }
        )

        if (response.success && response.data) {
          setInvitation(response.data)
          setUserEmail(response.data.email)
          setState('ready')
        } else {
          // Determine error type based on response
          const errorMsg = response.error || 'Failed to load invitation'

          if (errorMsg.includes('expired')) {
            setError({
              type: 'expired',
              message: 'This invitation link has expired. Request a new one from your organization admin.',
            })
          } else if (errorMsg.includes('not found')) {
            setError({
              type: 'invalid',
              message: 'This invitation link is invalid. It may have been revoked or already used.',
            })
          } else {
            setError({
              type: 'unknown',
              message: 'Could not verify invitation. Please try again or contact your organization admin.',
            })
          }
          setState('error')
        }
      } catch (err) {
        console.error('Error fetching invitation:', err)
        setError({
          type: 'unknown',
          message: 'An error occurred while loading the invitation. Please try again.',
        })
        setState('error')
      }
    }

    fetchInvitation()
  }, [token])

  /**
   * Handle countdown timer on success
   */
  useEffect(() => {
    if (state !== 'success') return

    if (countdown <= 0) {
      // Determine redirect location based on whether user has organizations
      const redirectPath =
        organizations && organizations.length > 0 ? '/dashboard' : '/org-setup'
      router.push(redirectPath)
      return
    }

    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown, state, router, organizations])

  /**
   * Handle accept invitation
   */
  const handleAccept = async () => {
    if (!token || !invitation) return

    try {
      setState('accepting')
      setError(null)

      const response: ApiResponse<AcceptanceResponse> = await apiClient.post(
        API_ENDPOINTS.invitations.accept(token),
        {},
        { enableRetry: false }
      )

      if (response.success && response.data) {
        // Refresh organizations context
        await refreshOrgs()
        setState('success')
      } else {
        const errorMsg = response.error || 'Failed to accept invitation'

        if (errorMsg.includes('already')) {
          setError({
            type: 'already_member',
            message: "You're already a member of this organization. Redirecting to dashboard...",
          })
          setTimeout(() => router.push('/dashboard'), 2000)
        } else if (errorMsg.includes('email')) {
          setError({
            type: 'email_mismatch',
            message:
              "Your email doesn't match this invitation. Please sign in with the correct account.",
          })
        } else if (errorMsg.includes('expired')) {
          setError({
            type: 'expired',
            message: 'This invitation has expired. Please request a new one.',
          })
        } else {
          setError({
            type: 'unknown',
            message: 'Could not accept invitation. Please try again.',
          })
        }
        setState('error')
      }
    } catch (err) {
      console.error('Error accepting invitation:', err)
      setError({
        type: 'unknown',
        message: 'An unexpected error occurred. Please try again.',
      })
      setState('error')
    }
  }

  /**
   * Handle decline invitation
   */
  const handleDecline = () => {
    router.push('/dashboard')
  }

  /**
   * Render loading state
   */
  if (state === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md p-8 border-4 border-black shadow-brutal-lg">
          <div className="flex flex-col items-center">
            <div
              className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black mb-4"
              role="status"
              aria-label="Loading"
            />
            <h1 className="text-2xl font-bold text-black">Verifying Invitation</h1>
            <p className="text-gray-600 mt-2 text-center">
              Please wait while we verify your invitation...
            </p>
          </div>
        </Card>
      </div>
    )
  }

  /**
   * Render success state
   */
  if (state === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md p-8 border-4 border-black shadow-brutal-lg">
          <div className="flex flex-col items-center text-center">
            <div className="mb-4 p-3 bg-green-50 rounded-full border-2 border-black">
              <IconCheck className="h-8 w-8 text-green-700" />
            </div>
            <h1 className="text-2xl font-bold text-black mb-2">Welcome!</h1>
            <p className="text-gray-700 mb-6">
              You're now a member of <span className="font-bold">{invitation?.org_name}</span>
            </p>
            <p className="text-sm text-gray-600 mb-4">
              Redirecting to dashboard in {countdown} {countdown === 1 ? 'second' : 'seconds'}...
            </p>
            <Button
              onClick={() =>
                router.push(
                  organizations && organizations.length > 0 ? '/dashboard' : '/org-setup'
                )
              }
              className="w-full font-bold"
            >
              Go to Dashboard Now
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  /**
   * Render error state
   */
  if (state === 'error' || error) {
    const getErrorColor = () => {
      if (error?.type === 'already_member') return 'bg-blue-50 border-blue-200'
      return 'bg-red-50 border-red-200'
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md p-8 border-4 border-black shadow-brutal-lg">
          <Alert className={`mb-6 border-2 border-black ${getErrorColor()}`}>
            <IconAlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-gray-900 font-medium">
              {error?.message || 'An error occurred. Please try again.'}
            </AlertDescription>
          </Alert>
          <div className="space-y-3">
            <Button
              onClick={() => router.push('/auth/login')}
              className="w-full font-bold"
            >
              Back to Login
            </Button>
            {error?.type === 'email_mismatch' && (
              <p className="text-xs text-gray-600 text-center">
                Try logging out and signing in with a different email address.
              </p>
            )}
          </div>
        </Card>
      </div>
    )
  }

  /**
   * Render ready state (invitation details showing)
   */
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md p-8 border-4 border-black shadow-brutal-lg">
        <div className="flex flex-col items-center mb-6">
          <OrangeLogo size="lg" />
          <h1 className="text-3xl font-bold mt-4 text-black">Join Organization</h1>
        </div>

        {invitation && (
          <div className="mb-8 space-y-4">
            <div className="bg-gray-50 border-2 border-black p-4 rounded">
              <p className="text-xs font-bold text-gray-600 uppercase mb-1">Organization</p>
              <p className="text-2xl font-bold text-black break-words">
                {invitation.org_name}
              </p>
            </div>

            <div className="bg-gray-50 border-2 border-black p-4 rounded">
              <p className="text-xs font-bold text-gray-600 uppercase mb-1">Your Role</p>
              <p className="text-lg font-bold text-black capitalize">{invitation.role}</p>
            </div>

            <div className="bg-gray-50 border-2 border-black p-4 rounded">
              <p className="text-xs font-bold text-gray-600 uppercase mb-1">Email</p>
              <p className="text-sm text-gray-700">{invitation.email}</p>
            </div>
          </div>
        )}

        {state === 'accepting' ? (
          <div className="flex justify-center py-4">
            <div
              className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-black"
              role="status"
              aria-label="Accepting invitation"
            />
          </div>
        ) : (
          <div className="space-y-3">
            <Button
              onClick={handleAccept}
              className="w-full bg-[#FF6B35] text-white font-bold border-2 border-black hover:shadow-brutal-lg"
              disabled={state === 'accepting'}
            >
              Accept Invitation
            </Button>
            <Button
              onClick={handleDecline}
              variant="outline"
              className="w-full border-2 border-black font-bold hover:shadow-brutal"
              disabled={state === 'accepting'}
            >
              Decline
            </Button>
          </div>
        )}

        <p className="text-xs text-gray-600 text-center mt-6">
          By accepting, you agree to join this organization and comply with its policies.
        </p>
      </Card>
    </div>
  )
}
