'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Card } from '@/components/ui/card'
import { AuthSplit } from '../AuthSplit'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'
import { useAuth } from '@/lib/api/hooks/useAuth'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

const MIN_PASSWORD = 12

interface Invitation {
  org_id: string
  org_name: string
  email: string
}

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { register, loading } = useAuth()
  const [form, setForm] = useState({ name: '', email: '', org_name: '', password: '', message: '' })
  const [requested, setRequested] = useState(false)
  const [sending, setSending] = useState(false)
  // /register?invite=<token>: create the account, then join the inviting organization.
  const [inviteToken, setInviteToken] = useState<string | null>(null)
  const [invitation, setInvitation] = useState<Invitation | null>(null)

  const set = (k: keyof typeof form, v: string) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('invite')
    if (!token) return
    setInviteToken(token)
    apiClient
      .get<Invitation>(API_ENDPOINTS.invitations.getDetails(token), { enableRetry: false })
      .then(res => {
        if (res.success && res.data) {
          setInvitation(res.data)
          setForm(f => ({ ...f, email: res.data!.email }))
        } else {
          router.replace(`/invitations/${token}`) // the invitation page explains what is wrong
        }
      })
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (inviteToken && invitation) {
        await register({ name: form.name, email: form.email, password: form.password, invitation_token: inviteToken })
        const accepted = await apiClient.post(API_ENDPOINTS.invitations.accept(inviteToken), {}, { enableRetry: false })
        if (!accepted.success) {
          // The account exists; the invitation page lets them retry.
          router.push(`/invitations/${inviteToken}`)
          return
        }
        localStorage.setItem('selected_org_id', invitation.org_id)
        router.push('/dashboard')
        return
      }
      setSending(true)
      const res = await apiClient.post(
        API_ENDPOINTS.auth.requestAccess,
        { name: form.name, email: form.email, org_name: form.org_name, message: form.message || undefined },
        { enableRetry: false },
      )
      if (!res.success) throw new Error(res.error || 'Please try again.')
      setRequested(true)
    } catch (err) {
      toast({
        title: inviteToken ? 'Could not create your account' : 'Could not send your request',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    } finally {
      setSending(false)
    }
  }

  const joining = Boolean(inviteToken)

  if (requested) {
    return (
      <AuthSplit>
        <Card className="w-full max-w-lg p-8 fm-card">
          <div className="flex flex-col items-center text-center">
            <OrangeLogo size="lg" />
            <h1 className="text-[24px] font-semibold tracking-tight mt-4">Request sent</h1>
            <p className="text-muted-foreground mt-2">
              We review every request. When yours is approved, an email to {form.email} will
              let you choose a password and sign in.
            </p>
            <a href="/login" className="mt-6 text-sm font-medium underline">Back to sign in</a>
          </div>
        </Card>
      </AuthSplit>
    )
  }

  return (
    <AuthSplit>
      <Card className="w-full max-w-lg p-8 fm-card">
        <div className="flex flex-col items-center mb-8">
          <OrangeLogo size="lg" />
          <h1 className="text-[24px] font-semibold tracking-tight mt-4">
            {joining ? `Join ${invitation?.org_name ?? 'your team'}` : 'Request access'}
          </h1>
          <p className="text-muted-foreground mt-2 text-center">
            {joining
              ? 'Create your account to accept the invitation.'
              : 'Tell us who you are. Once approved, you own the new organization and can invite your team.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full name</Label>
            <Input id="name" required autoComplete="name" value={form.name}
              onChange={e => set('name', e.target.value)} className="border border-[var(--fm-line)]" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" required type="email" autoComplete="email" value={form.email}
              readOnly={joining} aria-describedby={joining ? 'email-hint' : undefined}
              onChange={e => set('email', e.target.value)} className="border border-[var(--fm-line)]" />
            {joining && (
              <p id="email-hint" className="text-xs text-muted-foreground">The invitation was sent to this address.</p>
            )}
          </div>
          {!joining && (
            <div className="space-y-2">
              <Label htmlFor="org_name">Organization name</Label>
              <Input id="org_name" required autoComplete="organization" value={form.org_name}
                onChange={e => set('org_name', e.target.value)} className="border border-[var(--fm-line)]" />
            </div>
          )}
          {joining ? (
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" required type="password" autoComplete="new-password"
                minLength={MIN_PASSWORD} aria-describedby="password-hint" value={form.password}
                onChange={e => set('password', e.target.value)} className="border border-[var(--fm-line)]" />
              <p id="password-hint" className="text-xs text-muted-foreground">At least {MIN_PASSWORD} characters.</p>
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="message">What will you use FairMind for? (optional)</Label>
              <Textarea id="message" rows={3} value={form.message}
                onChange={e => set('message', e.target.value)} className="border border-[var(--fm-line)]" />
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading || sending || (joining && !invitation)}>
            {joining
              ? loading ? 'Creating account...' : 'Create account and join'
              : sending ? 'Sending request...' : 'Request access'}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{' '}
            <a
              href={inviteToken ? `/login?next=${encodeURIComponent(`/invitations/${inviteToken}`)}` : '/login'}
              className="font-bold underline"
            >
              Sign in
            </a>
          </p>
        </div>
      </Card>
    </AuthSplit>
  )
}
