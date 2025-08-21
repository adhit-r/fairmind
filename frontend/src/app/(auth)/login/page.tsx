"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/common/button"
import { Input } from "@/components/ui/common/input"
import { Label } from "@/components/ui/common/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Eye, EyeOff, Shield, Bot, Zap, Building2, UserPlus } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const router = useRouter()
  const { login, signUp } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (isSignUp) {
        const result = await signUp(email, password, fullName, organizationName)
        if (result.error) {
          setError(result.error.message)
        } else {
          router.push('/onboarding')
        }
      } else {
        const result = await login(email, password)
        if (result.success) {
          router.push('/dashboard')
        } else {
          setError(result.error || 'Login failed')
        }
      }
    } catch (error: any) {
      setError(error.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = () => {
    setEmail('demo@fairmind.xyz')
    setPassword('demo123')
    setIsSignUp(false)
  }

  const handleAdminLogin = () => {
    setEmail('admin@fairmind.app')
    setPassword('admin123')
    setIsSignUp(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <Shield className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            {isSignUp ? 'Create Account' : 'Welcome Back'}
          </CardTitle>
          <CardDescription>
            {isSignUp 
              ? 'Set up your organization and start managing AI governance'
              : 'Sign in to your Fairmind account'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>
            )}
            
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
            
            {isSignUp && (
              <div className="space-y-2">
                <Label htmlFor="organization">Organization Name</Label>
                <Input
                  id="organization"
                  type="text"
                  placeholder="Enter your organization name"
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  required
                />
              </div>
            )}
            
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
              {loading 
                ? (isSignUp ? "Creating Account..." : "Signing in...") 
                : (isSignUp ? "Create Account" : "Sign In")
              }
            </Button>
          </form>

          {/* Demo Login Buttons */}
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm text-muted-foreground mb-3 text-center">
              Try the demo:
            </p>
            <div className="space-y-2">
              <Button 
                variant="outline" 
                className="w-full" 
                onClick={handleDemoLogin}
                disabled={loading}
              >
                <Bot className="h-4 w-4 mr-2" />
                Demo Account
              </Button>
              <Button 
                variant="outline" 
                className="w-full" 
                onClick={handleAdminLogin}
                disabled={loading}
              >
                <Shield className="h-4 w-4 mr-2" />
                Admin Account
              </Button>
            </div>
          </div>

          {/* Toggle Sign Up/Login */}
          <div className="mt-6 text-center">
            <Button
              variant="link"
              onClick={() => setIsSignUp(!isSignUp)}
              disabled={loading}
            >
              {isSignUp ? (
                <>
                  Already have an account? Sign in
                </>
              ) : (
                <>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Don't have an account? Sign up
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 