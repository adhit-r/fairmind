'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { OrgProvider, useOrg } from '@/context/OrgContext'
import { AuthShell } from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { IconAlertTriangle, IconCircleCheck } from '@tabler/icons-react'

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

type PageState = 'loading' | 'ready' | 'accepting' | 'success' | 'error'

interface ErrorDetails {
  type: 'invalid' | 'expired' | 'email_mismatch' | 'already_member' | 'unknown'
  message: string
}

/**
 * Org Invitation Acceptance Page
 *
 * Flow: read the token from the URL, fetch invitation details, show the
 * organization / role / email, accept via POST /invitations/{token}/accept,
 * then continue to the dashboard.
 *
 * Handles invalid/expired tokens (400), email mismatch (403) and already a
 * member (409). Auth routes render outside the product shell, so this page
 * mounts its own OrgProvider.
 */
export default function InvitationPage() {
  return (
    <OrgProvider>
      <InvitationContent />
    </OrgProvider>
  )
}

function InvitationContent() {
  const params = useParams()
  const router = useRouter()
  const token = params?.token as string

  const { refreshOrgs } = useOrg()

  const [state, setState] = useState<PageState>('loading')
  const [error, setError] = useState<ErrorDetails | null>(null)
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null)
  const [countdown, setCountdown] = useState(2)

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
          setState('ready')
        } else {
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
              message: 'Could not verify the invitation. Please try again or contact your organization admin.',
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

  // Countdown to redirect after success
  useEffect(() => {
    if (state !== 'success') return

    if (countdown <= 0) {
      router.push('/dashboard')
      return
    }

    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown, state, router])

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
        await refreshOrgs()
        setState('success')
      } else {
        const errorMsg = response.error || 'Failed to accept invitation'

        if (errorMsg.includes('already')) {
          setError({
            type: 'already_member',
            message: 'You are already a member of this organization. Redirecting to the dashboard.',
          })
          setTimeout(() => router.push('/dashboard'), 2000)
        } else if (errorMsg.includes('email')) {
          setError({
            type: 'email_mismatch',
            message: 'Your email does not match this invitation. Sign in with the invited account.',
          })
        } else if (errorMsg.includes('expired')) {
          setError({
            type: 'expired',
            message: 'This invitation has expired. Please request a new one.',
          })
        } else {
          setError({
            type: 'unknown',
            message: 'Could not accept the invitation. Please try again.',
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

  if (state === 'loading') {
    return (
      <AuthShell title="Verifying invitation" description="Please wait while we check your invitation.">
        <div role="status" aria-live="polite" className="space-y-3">
          <span className="sr-only">Verifying invitation</span>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      </AuthShell>
    )
  }

  if (state === 'success') {
    return (
      <AuthShell title="Welcome">
        <div role="status" className="flex flex-col items-center text-center">
          <IconCircleCheck className="mb-3 h-10 w-10 text-success-strong" aria-hidden="true" />
          <p className="mb-2 text-sm text-foreground">
            You are now a member of <span className="font-semibold">{invitation?.org_name}</span>.
          </p>
          <p className="mb-5 text-xs text-muted-foreground">
            Continuing to the dashboard in {countdown} {countdown === 1 ? 'second' : 'seconds'}.
          </p>
          <Button onClick={() => router.push('/dashboard')} className="w-full">
            Go to dashboard now
          </Button>
        </div>
      </AuthShell>
    )
  }

  if (state === 'error' || error) {
    return (
      <AuthShell title="Invitation unavailable">
        <Alert variant={error?.type === 'already_member' ? 'info' : 'destructive'} className="mb-5">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription>{error?.message || 'An error occurred. Please try again.'}</AlertDescription>
        </Alert>
        <div className="space-y-3">
          <Button onClick={() => router.push('/login')} className="w-full">
            Back to sign in
          </Button>
          {error?.type === 'email_mismatch' && (
            <p className="text-center text-xs text-muted-foreground">
              Try signing out and signing in with the email address that received the invitation.
            </p>
          )}
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Join organization" description="You have been invited to collaborate in FairMind.">
      {invitation && (
        <dl className="mb-6 divide-y divide-border rounded-md border border-border">
          <div className="p-3">
            <dt className="text-xs font-medium text-muted-foreground">Organization</dt>
            <dd className="break-words text-base font-semibold text-foreground">{invitation.org_name}</dd>
          </div>
          <div className="p-3">
            <dt className="text-xs font-medium text-muted-foreground">Your role</dt>
            <dd className="text-sm font-medium capitalize text-foreground">{invitation.role}</dd>
          </div>
          <div className="p-3">
            <dt className="text-xs font-medium text-muted-foreground">Invited email</dt>
            <dd className="break-words text-sm text-foreground">{invitation.email}</dd>
          </div>
        </dl>
      )}

      <div className="space-y-3">
        <Button
          onClick={handleAccept}
          variant="action"
          className="w-full"
          disabled={state === 'accepting'}
          aria-busy={state === 'accepting'}
        >
          {state === 'accepting' ? 'Accepting...' : 'Accept invitation'}
        </Button>
        <Button
          onClick={() => router.push('/dashboard')}
          variant="outline"
          className="w-full"
          disabled={state === 'accepting'}
        >
          Decline
        </Button>
      </div>

      <p className="mt-6 text-center text-xs text-muted-foreground">
        By accepting, you agree to join this organization and follow its policies.
      </p>
    </AuthShell>
  )
}
