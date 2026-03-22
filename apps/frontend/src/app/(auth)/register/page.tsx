'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api/api-client'
import { IconCheck } from '@tabler/icons-react'

const ROLES = [
  { value: 'analyst', label: 'Analyst', description: 'Run bias evaluations and generate reports' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to models and reports' },
]

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    name: '',
    email: '',
    org_name: '',
    org_domain: '',
    requested_role: 'analyst',
    message: '',
  })

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await apiClient.post('/api/v1/register', form)
      setSubmitted(true)
    } catch (err: any) {
      toast({
        title: 'Request failed',
        description: err?.message || 'Please try again.',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md p-8 border-4 border-black shadow-brutal-lg text-center">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 rounded-full border-4 border-black bg-black flex items-center justify-center">
              <IconCheck className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-2xl font-bold mb-2">Request Submitted</h1>
          <p className="text-muted-foreground mb-6">
            Your access request has been sent for admin review. You'll receive an email once it's approved.
          </p>
          <Button variant="outline" className="border-2 border-black font-bold" onClick={() => router.push('/auth/login')}>
            Back to Login
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-lg p-8 border-2 border-black shadow-brutal-lg">
        <div className="flex flex-col items-center mb-8">
          <OrangeLogo size="lg" />
          <h1 className="text-3xl font-bold mt-4">Request Access</h1>
          <p className="text-muted-foreground mt-2 text-center">
            Fill in your details and an admin will review your request
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input required placeholder="Jane Smith" value={form.name}
                onChange={e => set('name', e.target.value)} className="border-2 border-black" />
            </div>
            <div className="space-y-2">
              <Label>Work Email</Label>
              <Input required type="email" placeholder="jane@acme.com" value={form.email}
                onChange={e => set('email', e.target.value)} className="border-2 border-black" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Organisation Name</Label>
              <Input required placeholder="Acme Corp" value={form.org_name}
                onChange={e => set('org_name', e.target.value)} className="border-2 border-black" />
            </div>
            <div className="space-y-2">
              <Label>Organisation Domain <span className="text-muted-foreground text-xs">(optional)</span></Label>
              <Input placeholder="acme.com" value={form.org_domain}
                onChange={e => set('org_domain', e.target.value)} className="border-2 border-black" />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Requested Role</Label>
            <div className="grid grid-cols-2 gap-3">
              {ROLES.map(r => (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => set('requested_role', r.value)}
                  className={`p-3 border-2 text-left transition-all ${
                    form.requested_role === r.value
                      ? 'border-black bg-black text-white shadow-brutal'
                      : 'border-black bg-white hover:shadow-brutal'
                  }`}
                >
                  <div className="font-bold text-sm">{r.label}</div>
                  <div className={`text-xs mt-1 ${form.requested_role === r.value ? 'text-gray-300' : 'text-muted-foreground'}`}>
                    {r.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Message to Admin <span className="text-muted-foreground text-xs">(optional)</span></Label>
            <textarea
              placeholder="Briefly describe your use case..."
              value={form.message}
              onChange={e => set('message', e.target.value)}
              rows={3}
              className="w-full border-2 border-black px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Submitting...' : 'Submit Access Request'}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Already have access?{' '}
            <a href="/auth/login" className="font-bold underline">Sign in</a>
          </p>
        </div>
      </Card>
    </div>
  )
}
