'use client'

import { useState } from 'react'
import Link from 'next/link'
import { AuthShell } from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiClient } from '@/lib/api/api-client'
import { cn } from '@/lib/utils'
import { IconAlertTriangle, IconCircleCheck } from '@tabler/icons-react'

const ROLES = [
  { value: 'analyst', label: 'Analyst', description: 'Run evaluations and generate reports' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to systems and reports' },
]

type FormState = {
  name: string
  email: string
  org_name: string
  org_domain: string
  requested_role: string
  message: string
}

export default function RegisterPage() {
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>({
    name: '',
    email: '',
    org_name: '',
    org_domain: '',
    requested_role: 'analyst',
    message: '',
  })

  const set = (key: keyof FormState, value: string) => setForm((current) => ({ ...current, [key]: value }))

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setSubmitError(null)
    try {
      await apiClient.post('/api/v1/register', form)
      setSubmitted(true)
    } catch (err: any) {
      setSubmitError(err?.message || 'The request could not be submitted. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <AuthShell title="Request submitted">
        <div role="status" className="flex flex-col items-center text-center">
          <IconCircleCheck className="mb-3 h-10 w-10 text-success-strong" aria-hidden="true" />
          <p className="mb-6 text-sm text-muted-foreground">
            Your access request has been sent for administrator review. You will receive an email once it is approved.
          </p>
          <Button asChild variant="outline">
            <Link href="/login">Back to sign in</Link>
          </Button>
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      wide
      title="Request access"
      description="Tell us who you are and an administrator will review your request."
      footer={
        <>
          Already have access?{' '}
          <Link href="/login" className="font-medium text-primary-strong underline underline-offset-4">
            Sign in
          </Link>
        </>
      }
    >
      {submitError && (
        <Alert variant="destructive" className="mb-5">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription>{submitError}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="reg-name">Full name</Label>
            <Input id="reg-name" required autoComplete="name" placeholder="Jane Smith" value={form.name} onChange={(e) => set('name', e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reg-email">Work email</Label>
            <Input id="reg-email" required type="email" autoComplete="email" placeholder="jane@company.com" value={form.email} onChange={(e) => set('email', e.target.value)} />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="reg-org">Organization name</Label>
            <Input id="reg-org" required autoComplete="organization" placeholder="Company name" value={form.org_name} onChange={(e) => set('org_name', e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reg-domain">Organization domain <span className="text-xs font-normal text-muted-foreground">(optional)</span></Label>
            <Input id="reg-domain" placeholder="company.com" value={form.org_domain} onChange={(e) => set('org_domain', e.target.value)} />
          </div>
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Requested role</legend>
          <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Requested role">
            {ROLES.map((role) => {
              const selected = form.requested_role === role.value
              return (
                <button
                  key={role.value}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => set('requested_role', role.value)}
                  className={cn(
                    'min-h-11 rounded-md border p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                    selected ? 'border-primary bg-primary-subtle' : 'border-input bg-card hover:bg-accent',
                  )}
                >
                  <span className="block text-sm font-semibold">{role.label}</span>
                  <span className="mt-0.5 block text-xs text-muted-foreground">{role.description}</span>
                </button>
              )
            })}
          </div>
        </fieldset>

        <div className="space-y-2">
          <Label htmlFor="reg-message">Message to administrator <span className="text-xs font-normal text-muted-foreground">(optional)</span></Label>
          <Textarea
            id="reg-message"
            placeholder="Briefly describe how you will use FairMind"
            value={form.message}
            onChange={(e) => set('message', e.target.value)}
            rows={3}
          />
        </div>

        <Button type="submit" variant="action" className="w-full" disabled={loading} aria-busy={loading}>
          {loading ? 'Submitting...' : 'Submit access request'}
        </Button>
      </form>
    </AuthShell>
  )
}
