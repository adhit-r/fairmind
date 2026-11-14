'use client'

import { useEffect, useState } from 'react'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

const MIN_PASSWORD = 12

export default function ResetPasswordPage() {
  const { toast } = useToast()
  // undefined while reading the link, null when it carries no token.
  const [token, setToken] = useState<string | null | undefined>(undefined)
  const [form, setForm] = useState({ password: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState<string | null>(null)
  const [welcome, setWelcome] = useState(false)

  useEffect(() => {
    // The emailed link carries the token in the fragment, which never reaches a server.
    // Keep the first read: the fragment is cleared from history below, and a repeated
    // effect run (React strict mode) would otherwise overwrite the token with null.
    const fragment = new URLSearchParams(window.location.hash.slice(1))
    const fromLink = fragment.get('token')
    setToken(current => current ?? fromLink)
    // Approval emails send new accounts here to choose their first password.
    if (fragment.get('welcome') === '1') setWelcome(true)
    window.history.replaceState(null, '', window.location.pathname)
  }, [])

  const set = (k: keyof typeof form, v: string) => setForm(f => ({ ...f, [k]: v }))
  const mismatch = form.confirm !== '' && form.confirm !== form.password

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || mismatch) return
    setLoading(true)
    const response: ApiResponse<{ message: string }> = await apiClient.post(
      API_ENDPOINTS.auth.resetPassword,
      { token, password: form.password },
      { enableRetry: false },
    )
    setLoading(false)
    if (response.success && response.data) {
      setDone(response.data.message)
    } else {
      toast({
        title: 'Could not change your password',
        description: response.error || 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md p-8 fm-card">
        <div className="flex flex-col items-center mb-8">
          <OrangeLogo size="lg" />
          <h1 className="text-[24px] font-semibold tracking-tight mt-4">{welcome ? 'Welcome to FairMind' : 'Choose a new password'}</h1>
          {welcome && <p className="text-muted-foreground mt-2 text-center">Your access was approved. Choose a password to finish setting up your account.</p>}
        </div>

        {done ? (
          <div className="space-y-4 text-center">
            <p role="status" className="text-sm">{done}</p>
            <a href="/login" className="inline-block px-4 py-2 border border-[var(--fm-line)] font-medium text-sm">
              Sign in
            </a>
          </div>
        ) : token === null ? (
          <p role="alert" className="text-sm text-destructive text-center">
            This reset link is incomplete.{' '}
            <a href="/forgot-password" className="font-bold underline">Request a new one</a>.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="password">New password</Label>
              <Input id="password" required type="password" autoComplete="new-password"
                minLength={MIN_PASSWORD} aria-describedby="password-hint" value={form.password}
                onChange={e => set('password', e.target.value)} className="border border-[var(--fm-line)]" />
              <p id="password-hint" className="text-xs text-muted-foreground">At least {MIN_PASSWORD} characters.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm">Repeat the new password</Label>
              <Input id="confirm" required type="password" autoComplete="new-password"
                aria-invalid={mismatch} aria-describedby={mismatch ? 'confirm-error' : undefined} value={form.confirm}
                onChange={e => set('confirm', e.target.value)} className="border border-[var(--fm-line)]" />
              {mismatch && (
                <p id="confirm-error" className="text-sm text-destructive">The two passwords do not match.</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={loading || !token || mismatch}>
              {loading ? 'Saving...' : welcome ? 'Set password and continue' : 'Set new password'}
            </Button>
          </form>
        )}
      </Card>
    </div>
  )
}
