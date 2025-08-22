"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/common/button"
import { Input } from "@/components/ui/common/input"
import { Label } from "@/components/ui/common/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Eye, EyeOff, Shield, Bot, Zap, ArrowLeft } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const router = useRouter()
  const { signUp } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    // Validation
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long')
      setLoading(false)
      return
    }

    try {
      const result = await signUp(email, password, fullName, organizationName)
      if (result.error) {
        setError(result.error.message || 'Signup failed')
      } else {
        setSuccess('Account created successfully! Please check your email to verify your account.')
        // Redirect to login after a short delay
        setTimeout(() => {
          router.push('/login')
        }, 3000)
      }
    } catch (error: any) {
      setError(error.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="h-12 w-12 bg-primary rounded-xl flex items-center justify-center">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">FairMind</h1>
              <p className="text-sm text-muted-foreground">AI Governance Platform</p>
            </div>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">
            Create Account
          </h2>
          <p className="text-muted-foreground">
            Sign up to get started with AI governance
          </p>
        </div>

        {/* Signup Form */}
        <Card className="border-border/50">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Sign up</CardTitle>
            <CardDescription className="text-center">
              Create your account to access the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              {success && (
                <Alert>
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  className="bg-background border-border"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="organizationName">Organization Name</Label>
                <Input
                  id="organizationName"
                  type="text"
                  placeholder="Enter your organization name"
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  required
                  className="bg-background border-border"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-background border-border"
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
                    className="bg-background border-border pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="bg-background border-border pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
              </div>
              
              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading}
              >
                {loading ? "Creating account..." : "Create account"}
              </Button>
            </form>
            
            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link href="/login" className="text-primary hover:underline">
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="text-center space-y-2">
            <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center mx-auto">
              <Shield className="h-4 w-4 text-primary" />
            </div>
            <h3 className="text-sm font-medium text-foreground">AI Governance</h3>
            <p className="text-xs text-muted-foreground">Comprehensive oversight</p>
          </div>
          <div className="text-center space-y-2">
            <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center mx-auto">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <h3 className="text-sm font-medium text-foreground">Model Testing</h3>
            <p className="text-xs text-muted-foreground">Bias detection & validation</p>
          </div>
          <div className="text-center space-y-2">
            <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center mx-auto">
              <Zap className="h-4 w-4 text-primary" />
            </div>
            <h3 className="text-sm font-medium text-foreground">Real-time Monitoring</h3>
            <p className="text-xs text-muted-foreground">Live compliance tracking</p>
          </div>
        </div>
      </div>
    </div>
  )
}
