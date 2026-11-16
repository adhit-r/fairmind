'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/api/hooks/useAuth'
import { useAuthentik } from '@/lib/api/hooks/useAuthentik'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AuthShell } from '@/components/auth/AuthShell'
import { useToast } from '@/hooks/use-toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema, type LoginFormData } from '@/lib/validations/schemas'
import { IconAlertTriangle, IconLogin2 } from '@tabler/icons-react'

const AUTHENTIK_ENABLED = !!process.env.NEXT_PUBLIC_AUTHENTIK_URL

export default function LoginPage() {
  const router = useRouter()
  const { login, loading, error } = useAuth()
  const { login: authentikLogin, isLoading: ssoLoading } = useAuthentik()
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data)
      toast({
        title: 'Signed in',
        description: 'Welcome back.',
      })
      router.push('/dashboard')
    } catch (err) {
      toast({
        title: 'Sign-in failed',
        description: err instanceof Error ? err.message : 'Invalid credentials',
        variant: 'destructive',
      })
    }
  }

  return (
    <AuthShell
      title="Sign in to FairMind"
      description="Govern, evaluate and evidence your AI systems."
      footer={
        <>
          Need access?{' '}
          <Link href="/register" className="font-medium text-primary-strong underline underline-offset-4">
            Request access
          </Link>
        </>
      }
    >
      {error && (
        <Alert variant="destructive" className="mb-5">
          <IconAlertTriangle aria-hidden="true" />
          <AlertDescription>
            {error.message || 'Unable to sign in. Check your email and password, or contact your administrator.'}
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? 'email-error' : undefined}
            {...register('email')}
          />
          {errors.email && (
            <p id="email-error" role="alert" className="text-sm font-medium text-destructive-strong">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={errors.password ? 'password-error' : undefined}
            {...register('password')}
          />
          {errors.password && (
            <p id="password-error" role="alert" className="text-sm font-medium text-destructive-strong">{errors.password.message}</p>
          )}
        </div>

        <Button type="submit" variant="action" className="w-full" disabled={loading} aria-busy={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </Button>
      </form>

      {AUTHENTIK_ENABLED && (
        <>
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-card px-3 text-muted-foreground">or</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => authentikLogin()}
            disabled={ssoLoading}
          >
            <IconLogin2 aria-hidden="true" />
            {ssoLoading ? 'Redirecting...' : 'Continue with single sign-on'}
          </Button>
        </>
      )}
    </AuthShell>
  )
}
