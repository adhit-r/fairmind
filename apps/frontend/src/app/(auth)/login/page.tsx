'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/api/hooks/useAuth'
import { useAuthentik } from '@/lib/api/hooks/useAuthentik'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { OrangeLogo } from '@/components/OrangeLogo'
import { useToast } from '@/hooks/use-toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema, type LoginFormData } from '@/lib/validations/schemas'
import { IconAlertTriangle, IconBrandGoogle } from '@tabler/icons-react'

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
        title: "Login successful",
        description: "Welcome back!",
      })
      router.push('/dashboard')
    } catch (err) {
      toast({
        title: "Login failed",
        description: err instanceof Error ? err.message : "Invalid credentials",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md p-8 border-2 border-black shadow-brutal-lg">
        <div className="flex flex-col items-center mb-8">
          <OrangeLogo size="lg" />
          <h1 className="text-3xl font-bold mt-4">FairMind</h1>
          <p className="text-muted-foreground mt-2">Access Your AI Governance Hub</p>
        </div>

        {error && (
          <Alert className="mb-6 border-2 border-black shadow-brutal-lg bg-background">
            <IconAlertTriangle className="h-4 w-4 text-destructive" />
            <AlertDescription className="text-destructive font-medium">
              {error.message || 'Unable to sign in. Please check your email and password, or contact support.'}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              aria-describedby={errors.email ? "email-error" : undefined}
              {...register('email')}
              className="border-2 border-black"
            />
            {errors.email && (
              <p id="email-error" className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <Label htmlFor="password">Password</Label>
              <a href="/forgot-password" className="text-xs text-muted-foreground hover:underline">
                Forgot password?
              </a>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              aria-describedby={errors.password ? "password-error" : undefined}
              {...register('password')}
              className="border-2 border-black"
            />
            {errors.password && (
              <p id="password-error" className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
            aria-busy={loading}
            aria-label={loading ? 'Signing in, please wait' : 'Sign in to FairMind'}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        {AUTHENTIK_ENABLED && (
          <>
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t-2 border-black" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 font-bold text-muted-foreground">or</span>
              </div>
            </div>

            <Button
              type="button"
              variant="neutral"
              className="w-full border-2 border-black font-bold hover:shadow-brutal"
              onClick={() => authentikLogin()}
              disabled={ssoLoading}
            >
              <IconBrandGoogle className="mr-2 h-4 w-4" />
              {ssoLoading ? 'Redirecting...' : 'Continue with SSO'}
            </Button>
          </>
        )}

        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground mb-3">Don't have an account?</p>
          <a href="/register" className="inline-block px-4 py-2 border-2 border-black font-medium hover:shadow-brutal text-sm">
            Request Access
          </a>
        </div>
      </Card>
    </div>
  )
}
