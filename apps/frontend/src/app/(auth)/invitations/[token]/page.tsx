'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { OrangeLogo } from '@/components/OrangeLogo'
import { IconAlertTriangle } from '@tabler/icons-react'

interface InvitationDetails {
  org_id: string
  org_name: string
  email: string
  role: string
  expires_at: string
}

type PageState = 'loading' | 'ready' | 'accepting' | 'error'

/**
 * Accept an organization invitation.
 *
 * Anyone with the link sees the organization, role and invited email. A signed-in
 * user accepts here; a signed-out one signs in (and is sent back here) or creates
 * an account that joins the organization instead of starting a new one.
 * This page sits outside the dashboard providers, so it reads no org context.
 */
export default function InvitationPage() {
  const params = useParams()
  const router = useRouter()
  const token = params?.token as string
  const here = `/invitations/${token}`

  const [state, setState] = useState<PageState>('loading')
  const [error, setError] = useState<string | null>(null)
  const [emailMismatch, setEmailMismatch] = useState(false)
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    setSignedIn(Boolean(localStorage.getItem('access_token')))
    if (!token) {
      setError('This invitation link is incomplete.')
      setState('error')
      return
    }
    apiClient
      .get<InvitationDetails>(API_ENDPOINTS.invitations.getDetails(token), { enableRetry: false })
      .then(res => {
        if (res.success && res.data) {
          setInvitation(res.data)
          setState('ready')
          return
        }
        const msg = res.error || ''
        setError(
          msg.includes('expired')
            ? 'This invitation has expired. Ask your organization admin for a new one.'
            : 'This invitation link is not valid. It may have been revoked or already used.'
        )
        setState('error')
      })
      .catch(() => {
        setError('Could not load the invitation. Check your connection and try again.')
        setState('error')
      })
  }, [token])

  const accept = async () => {
    if (!invitation) return
    setState('accepting')
    setError(null)
    const res = await apiClient.post(API_ENDPOINTS.invitations.accept(token), {}, { enableRetry: false })
    const msg = res.error || ''
    if (res.success || msg.includes('already a member')) {
      localStorage.setItem('selected_org_id', invitation.org_id)
      router.push('/dashboard')
      return
    }
    setEmailMismatch(msg.includes('email'))
    setError(
      msg.includes('email')
        ? `This invitation is for ${invitation.email}. Sign in with that account to accept it.`
        : msg.includes('expired')
          ? 'This invitation has expired. Ask your organization admin for a new one.'
          : msg.includes('already')
            ? 'This invitation has already been used.'
            : 'Could not accept the invitation. Try again.'
    )
    setState('ready')
  }

  const signInHref = `/login?next=${encodeURIComponent(here)}`

  if (state === 'loading') {
    return (
      <Shell>
        <div className="flex flex-col items-center py-6" role="status">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--fm-line)] border-t-[var(--fm-ink)]" aria-hidden />
          <p className="mt-4 text-sm text-[var(--fm-ink2)]">Checking your invitation</p>
        </div>
      </Shell>
    )
  }

  if (state === 'error' || !invitation) {
    return (
      <Shell>
        <ErrorNote message={error} />
        <Button onClick={() => router.push(signedIn ? '/dashboard' : '/login')} className="w-full">
          {signedIn ? 'Go to dashboard' : 'Sign in'}
        </Button>
      </Shell>
    )
  }

  return (
    <Shell>
      <div className="flex flex-col items-center mb-6 text-center">
        <OrangeLogo size="lg" />
        <h1 className="text-[24px] font-semibold tracking-tight mt-4 text-[var(--fm-ink)]">
          Join {invitation.org_name}
        </h1>
        <p className="mt-2 text-sm text-[var(--fm-ink2)]">
          You are invited as <span className="font-semibold capitalize">{invitation.role}</span>.
        </p>
      </div>

      <dl className="mb-6 rounded-[10px] border border-[var(--fm-line)] p-4 text-sm">
        <dt className="text-xs font-semibold text-[var(--fm-ink2)]">Invited email</dt>
        <dd className="mt-1 text-[var(--fm-ink)] break-all">{invitation.email}</dd>
      </dl>

      {error && <ErrorNote message={error} />}

      {signedIn ? (
        <div className="space-y-3">
          <Button onClick={accept} className="w-full" disabled={state === 'accepting'} aria-busy={state === 'accepting'}>
            {state === 'accepting' ? 'Joining...' : 'Accept invitation'}
          </Button>
          {emailMismatch ? (
            <Button variant="neutral" className="w-full border border-[var(--fm-line)]"
              onClick={() => { apiClient.clearSession(); router.push(signInHref) }}>
              Sign in with a different account
            </Button>
          ) : (
            <Button variant="neutral" className="w-full border border-[var(--fm-line)]" onClick={() => router.push('/dashboard')}>
              Not now
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <Button className="w-full" onClick={() => router.push(`/register?invite=${encodeURIComponent(token)}`)}>
            Create account and join
          </Button>
          <Button variant="neutral" className="w-full border border-[var(--fm-line)]" onClick={() => router.push(signInHref)}>
            I already have an account
          </Button>
        </div>
      )}
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen flex items-center justify-center bg-[var(--fm-bg)] p-4">
      <Card className="w-full max-w-md p-8 fm-card">{children}</Card>
    </main>
  )
}

function ErrorNote({ message }: { message: string | null }) {
  return (
    <Alert className="mb-4 border border-[var(--fm-line)]" role="alert">
      <IconAlertTriangle className="h-4 w-4 text-red-600" aria-hidden />
      <AlertDescription className="text-[var(--fm-ink)]">{message || 'Something went wrong. Try again.'}</AlertDescription>
    </Alert>
  )
}
