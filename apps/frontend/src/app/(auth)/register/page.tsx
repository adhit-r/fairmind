'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Card } from '@/components/ui/card'
import { AuthSplit } from '../AuthSplit'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { useAuth } from '@/lib/api/hooks/useAuth'

const MIN_PASSWORD = 12

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { register, loading } = useAuth()
  const [form, setForm] = useState({ name: '', email: '', org_name: '', password: '' })

  const set = (k: keyof typeof form, v: string) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await register(form)
      router.push('/onboard')
    } catch (err) {
      toast({
        title: 'Could not create your account',
        description: err instanceof Error ? err.message : 'Please try again.',
        variant: 'destructive',
      })
    }
  }

  return (
    <AuthSplit>
      <Card className="w-full max-w-lg p-8 fm-card">
        <div className="flex flex-col items-center mb-8">
          <OrangeLogo size="lg" />
          <h1 className="text-[24px] font-semibold tracking-tight mt-4">Create your organization</h1>
          <p className="text-muted-foreground mt-2 text-center">
            You will own the new organization and can invite your team after setup.
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
              onChange={e => set('email', e.target.value)} className="border border-[var(--fm-line)]" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="org_name">Organization name</Label>
            <Input id="org_name" required autoComplete="organization" value={form.org_name}
              onChange={e => set('org_name', e.target.value)} className="border border-[var(--fm-line)]" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" required type="password" autoComplete="new-password"
              minLength={MIN_PASSWORD} aria-describedby="password-hint" value={form.password}
              onChange={e => set('password', e.target.value)} className="border border-[var(--fm-line)]" />
            <p id="password-hint" className="text-xs text-muted-foreground">At least {MIN_PASSWORD} characters.</p>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{' '}
            <a href="/login" className="font-bold underline">Sign in</a>
          </p>
        </div>
      </Card>
    </AuthSplit>
  )
}
