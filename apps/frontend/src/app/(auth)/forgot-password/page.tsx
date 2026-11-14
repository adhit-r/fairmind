'use client'

import { HumanCheck, awaitingHumanCheck, humanCheckHeaders } from '@/components/auth/HumanCheck'
import { useState } from 'react'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

export default function ForgotPasswordPage() {
  const { toast } = useToast()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [check, setCheck] = useState<string | null>(null)
  const [checkRound, setCheckRound] = useState(0)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    const response: ApiResponse<{ message: string }> = await apiClient.post(
      API_ENDPOINTS.auth.requestPasswordReset,
      { email },
      { enableRetry: false, headers: humanCheckHeaders(check) },
    )
    setLoading(false)
    setCheckRound((n) => n + 1)
    if (response.success && response.data) {
      setAnswer(response.data.message)
    } else {
      toast({
        title: 'Could not send a reset link',
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
          <h1 className="text-[24px] font-semibold tracking-tight mt-4">Reset your password</h1>
          <p className="text-muted-foreground mt-2 text-center">
            Enter the email you sign in with and we will send you a link to choose a new password.
          </p>
        </div>

        {answer ? (
          <p role="status" className="text-sm">{answer}</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" required type="email" autoComplete="email" value={email}
                onChange={e => setEmail(e.target.value)} className="border border-[var(--fm-line)]" />
            </div>

            <HumanCheck onToken={setCheck} resetKey={checkRound} />
            <Button type="submit" className="w-full" disabled={loading || awaitingHumanCheck(check)}>
              {loading ? 'Sending...' : 'Send reset link'}
            </Button>
          </form>
        )}

        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Remembered it?{' '}
            <a href="/login" className="font-bold underline">Sign in</a>
          </p>
        </div>
      </Card>
    </div>
  )
}
