"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/common/button"
import { Input } from "@/components/ui/common/input"
import { Label } from "@/components/ui/common/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Eye, EyeOff, Shield, Bot, Zap, Building2 } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await login(email, password)
      if (result.success) {
        // Check if this is a test organization
        if (email.includes('demo') || email.includes('test')) {
          // Redirect to dashboard with test data
          router.push('/dashboard?org=test')
        } else {
          // Redirect to onboarding for new organizations
          router.push('/onboarding')
        }
      } else {
        setError(result.error || 'Login failed')
      }
    } catch (error: any) {
      setError(error.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = () => {
    setEmail('demo@fairmind.xyz')
    setPassword('demo123')
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-2xl font-bold">Welcome to Fairmind</h1>
          <p className="text-muted-foreground mt-2">
            AI Governance Platform
          </p>
        </div>

        {/* Login Form */}
        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access your AI governance dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Signing in..." : "Sign In"}
              </Button>
            </form>

            {/* Demo Login */}
            <div className="mt-6 pt-6 border-t">
              <Button 
                variant="outline" 
                className="w-full" 
                onClick={handleDemoLogin}
              >
                <Building2 className="h-4 w-4 mr-2" />
                Try Demo (Test Data)
              </Button>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Demo includes sample models, bias analyses, and compliance data
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center space-y-2">
          <p className="text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link href="/signup" className="text-primary hover:underline">
              Sign up
            </Link>
          </p>
          <Link href="/forgot-password" className="text-sm text-muted-foreground hover:underline">
            Forgot your password?
          </Link>
        </div>

        {/* Features Preview */}
        <div className="grid grid-cols-3 gap-4 mt-8">
          <div className="text-center p-4 bg-muted rounded-lg">
            <Bot className="h-6 w-6 mx-auto mb-2 text-primary" />
            <p className="text-xs font-medium">Bias Detection</p>
          </div>
          <div className="text-center p-4 bg-muted rounded-lg">
            <Shield className="h-6 w-6 mx-auto mb-2 text-primary" />
            <p className="text-xs font-medium">Security Testing</p>
          </div>
          <div className="text-center p-4 bg-muted rounded-lg">
            <Zap className="h-6 w-6 mx-auto mb-2 text-primary" />
            <p className="text-xs font-medium">Compliance</p>
          </div>
        </div>
      </div>
    </div>
  )
} 