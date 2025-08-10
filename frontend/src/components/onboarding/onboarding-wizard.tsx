"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { 
  Shield, 
  Bot, 
  Zap, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle, 
  Users, 
  Building,
  Settings,
  FileText,
  Target,
  BarChart3,
  Lock,
  Globe,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  TrendingUp,
  AlertTriangle,
  Info
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"

interface OnboardingStep {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  required: boolean
  completed: boolean
}

interface OrganizationData {
  name: string
  industry: string
  size: string
  complianceFrameworks: string[]
  primaryUseCase: string
}

interface UserProfileData {
  role: string
  department: string
  experience: string
  goals: string[]
}

export function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [organizationData, setOrganizationData] = useState<OrganizationData>({
    name: '',
    industry: '',
    size: '',
    complianceFrameworks: [],
    primaryUseCase: ''
  })
  const [userProfileData, setUserProfileData] = useState<UserProfileData>({
    role: '',
    department: '',
    experience: '',
    goals: []
  })
  const [complianceGoals, setComplianceGoals] = useState<string[]>([])
  const [notificationPreferences, setNotificationPreferences] = useState({
    email: true,
    inApp: true,
    weekly: false,
    critical: true
  })

  const { profile, updateProfile } = useAuth()
  const router = useRouter()

  const steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to Fairmind',
      description: 'Let\'s get you started with AI governance',
      icon: <Shield className="h-6 w-6" />,
      required: true,
      completed: false
    },
    {
      id: 'organization',
      title: 'Organization Setup',
      description: 'Tell us about your organization',
      icon: <Building className="h-6 w-6" />,
      required: true,
      completed: false
    },
    {
      id: 'profile',
      title: 'Your Role',
      description: 'Help us personalize your experience',
      icon: <Users className="h-6 w-6" />,
      required: true,
      completed: false
    },
    {
      id: 'compliance',
      title: 'Compliance Goals',
      description: 'What regulations are you targeting?',
      icon: <Target className="h-6 w-6" />,
      required: false,
      completed: false
    },
    {
      id: 'preferences',
      title: 'Preferences',
      description: 'Customize your experience',
      icon: <Settings className="h-6 w-6" />,
      required: false,
      completed: false
    },
    {
      id: 'complete',
      title: 'You\'re All Set!',
      description: 'Ready to start your AI governance journey',
      icon: <CheckCircle className="h-6 w-6" />,
      required: true,
      completed: false
    }
  ]

  const industries = [
    'Technology',
    'Healthcare',
    'Finance',
    'Education',
    'Manufacturing',
    'Retail',
    'Government',
    'Non-profit',
    'Other'
  ]

  const companySizes = [
    '1-10 employees',
    '11-50 employees',
    '51-200 employees',
    '201-1000 employees',
    '1000+ employees'
  ]

  const roles = [
    'AI Governance Manager',
    'Data Scientist',
    'Compliance Officer',
    'Risk Manager',
    'IT Director',
    'Legal Counsel',
    'Executive',
    'Other'
  ]

  const departments = [
    'AI/ML',
    'Data Science',
    'Compliance',
    'Risk Management',
    'IT',
    'Legal',
    'Operations',
    'Other'
  ]

  const experienceLevels = [
    'Beginner (0-2 years)',
    'Intermediate (3-5 years)',
    'Advanced (6-10 years)',
    'Expert (10+ years)'
  ]

  const complianceFrameworks = [
    'EU AI Act',
    'GDPR',
    'CCPA',
    'NIST AI Risk Management',
    'ISO 42001',
    'IEEE 2857',
    'Custom Framework'
  ]

  const useCases = [
    'Bias Detection & Mitigation',
    'Model Explainability',
    'Security Testing',
    'Compliance Monitoring',
    'Risk Assessment',
    'Audit Preparation',
    'All of the above'
  ]

  const goalOptions = [
    'Improve model fairness',
    'Ensure regulatory compliance',
    'Reduce AI risks',
    'Build trust with stakeholders',
    'Automate governance processes',
    'Prepare for audits',
    'Train team on AI governance'
  ]

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = async () => {
    setLoading(true)
    setError('')

    try {
      // Update user profile with onboarding data
      await updateProfile({
        onboarding_completed: true,
        organization: organizationData,
        role: userProfileData.role,
        department: userProfileData.department,
        experience: userProfileData.experience,
        goals: userProfileData.goals,
        compliance_goals: complianceGoals,
        notification_preferences: notificationPreferences
      })

      // Navigate to dashboard
      router.push('/dashboard')
    } catch (error: any) {
      setError(error.message || 'Failed to complete onboarding')
    } finally {
      setLoading(false)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <div className="mx-auto h-20 w-20 bg-primary/10 rounded-full flex items-center justify-center">
                <Shield className="h-10 w-10 text-primary" />
              </div>
              <h2 className="text-2xl font-bold">Welcome to Fairmind</h2>
              <p className="text-muted-foreground max-w-md mx-auto">
                Your comprehensive AI governance platform for bias detection, security testing, and compliance monitoring.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="text-center p-4">
                <Bot className="h-8 w-8 mx-auto mb-2 text-primary" />
                <h3 className="font-semibold">AI Model Management</h3>
                <p className="text-sm text-muted-foreground">Register and track your AI models</p>
              </Card>
              <Card className="text-center p-4">
                <Target className="h-8 w-8 mx-auto mb-2 text-primary" />
                <h3 className="font-semibold">Bias Detection</h3>
                <p className="text-sm text-muted-foreground">Identify and mitigate model bias</p>
              </Card>
              <Card className="text-center p-4">
                <Lock className="h-8 w-8 mx-auto mb-2 text-primary" />
                <h3 className="font-semibold">Security Testing</h3>
                <p className="text-sm text-muted-foreground">OWASP security analysis</p>
              </Card>
            </div>

            <div className="text-center">
              <Button onClick={handleNext} className="w-full md:w-auto">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )

      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">Organization Setup</h2>
              <p className="text-muted-foreground">
                Tell us about your organization to customize your experience
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="orgName">Organization Name *</Label>
                <Input
                  id="orgName"
                  placeholder="Enter your organization name"
                  value={organizationData.name}
                  onChange={(e) => setOrganizationData({...organizationData, name: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="industry">Industry *</Label>
                <Select value={organizationData.industry} onValueChange={(value) => setOrganizationData({...organizationData, industry: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your industry" />
                  </SelectTrigger>
                  <SelectContent>
                    {industries.map((industry) => (
                      <SelectItem key={industry} value={industry}>{industry}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="size">Company Size *</Label>
                <Select value={organizationData.size} onValueChange={(value) => setOrganizationData({...organizationData, size: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select company size" />
                  </SelectTrigger>
                  <SelectContent>
                    {companySizes.map((size) => (
                      <SelectItem key={size} value={size}>{size}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Primary Use Case *</Label>
                <Select value={organizationData.primaryUseCase} onValueChange={(value) => setOrganizationData({...organizationData, primaryUseCase: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select primary use case" />
                  </SelectTrigger>
                  <SelectContent>
                    {useCases.map((useCase) => (
                      <SelectItem key={useCase} value={useCase}>{useCase}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={handlePrevious}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNext} disabled={!organizationData.name || !organizationData.industry || !organizationData.size || !organizationData.primaryUseCase}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">Your Role</h2>
              <p className="text-muted-foreground">
                Help us personalize your experience based on your role
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="role">Your Role *</Label>
                <Select value={userProfileData.role} onValueChange={(value) => setUserProfileData({...userProfileData, role: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your role" />
                  </SelectTrigger>
                  <SelectContent>
                    {roles.map((role) => (
                      <SelectItem key={role} value={role}>{role}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="department">Department</Label>
                <Select value={userProfileData.department} onValueChange={(value) => setUserProfileData({...userProfileData, department: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map((dept) => (
                      <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="experience">Experience Level</Label>
                <Select value={userProfileData.experience} onValueChange={(value) => setUserProfileData({...userProfileData, experience: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select experience level" />
                  </SelectTrigger>
                  <SelectContent>
                    {experienceLevels.map((level) => (
                      <SelectItem key={level} value={level}>{level}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Your Goals (Select all that apply)</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {goalOptions.map((goal) => (
                    <div key={goal} className="flex items-center space-x-2">
                      <Checkbox
                        id={goal}
                        checked={userProfileData.goals.includes(goal)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setUserProfileData({
                              ...userProfileData,
                              goals: [...userProfileData.goals, goal]
                            })
                          } else {
                            setUserProfileData({
                              ...userProfileData,
                              goals: userProfileData.goals.filter(g => g !== goal)
                            })
                          }
                        }}
                      />
                      <Label htmlFor={goal} className="text-sm">{goal}</Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={handlePrevious}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNext} disabled={!userProfileData.role}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">Compliance Goals</h2>
              <p className="text-muted-foreground">
                Select the compliance frameworks you're targeting (optional)
              </p>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {complianceFrameworks.map((framework) => (
                  <div key={framework} className="flex items-center space-x-2">
                    <Checkbox
                      id={framework}
                      checked={complianceGoals.includes(framework)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setComplianceGoals([...complianceGoals, framework])
                        } else {
                          setComplianceGoals(complianceGoals.filter(f => f !== framework))
                        }
                      }}
                    />
                    <Label htmlFor={framework} className="text-sm">{framework}</Label>
                  </div>
                ))}
              </div>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  You can always update your compliance goals later in your settings.
                </AlertDescription>
              </Alert>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={handlePrevious}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNext}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">Preferences</h2>
              <p className="text-muted-foreground">
                Customize your notification and experience preferences
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-3">
                <Label>Notification Preferences</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="email"
                      checked={notificationPreferences.email}
                      onCheckedChange={(checked) => setNotificationPreferences({...notificationPreferences, email: !!checked})}
                    />
                    <Label htmlFor="email" className="text-sm">Email notifications</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="inApp"
                      checked={notificationPreferences.inApp}
                      onCheckedChange={(checked) => setNotificationPreferences({...notificationPreferences, inApp: !!checked})}
                    />
                    <Label htmlFor="inApp" className="text-sm">In-app notifications</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="weekly"
                      checked={notificationPreferences.weekly}
                      onCheckedChange={(checked) => setNotificationPreferences({...notificationPreferences, weekly: !!checked})}
                    />
                    <Label htmlFor="weekly" className="text-sm">Weekly summary reports</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="critical"
                      checked={notificationPreferences.critical}
                      onCheckedChange={(checked) => setNotificationPreferences({...notificationPreferences, critical: !!checked})}
                    />
                    <Label htmlFor="critical" className="text-sm">Critical alerts only</Label>
                  </div>
                </div>
              </div>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  You can modify these preferences anytime in your account settings.
                </AlertDescription>
              </Alert>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={handlePrevious}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNext}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <div className="mx-auto h-20 w-20 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-10 w-10 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold">You're All Set!</h2>
              <p className="text-muted-foreground">
                Your Fairmind account is ready. Let's start your AI governance journey.
              </p>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">What's Next?</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-primary">1</span>
                    </div>
                    <div>
                      <p className="font-medium">Upload your first AI model</p>
                      <p className="text-sm text-muted-foreground">Start by registering a model in your inventory</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-primary">2</span>
                    </div>
                    <div>
                      <p className="font-medium">Run your first analysis</p>
                      <p className="text-sm text-muted-foreground">Test for bias, security, or compliance issues</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-primary">3</span>
                    </div>
                    <div>
                      <p className="font-medium">Explore the dashboard</p>
                      <p className="text-sm text-muted-foreground">Monitor your AI governance metrics</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={handlePrevious}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleComplete} disabled={loading}>
                {loading ? "Setting up..." : "Get Started"}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="h-12 w-12 bg-primary rounded-xl flex items-center justify-center">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Fairmind</h1>
              <p className="text-sm text-muted-foreground">AI Governance Platform</p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Step {currentStep + 1} of {steps.length}</span>
            <span>{Math.round(((currentStep + 1) / steps.length) * 100)}% Complete</span>
          </div>
          <Progress value={((currentStep + 1) / steps.length) * 100} className="h-2" />
        </div>

        {/* Step Indicator */}
        <div className="flex justify-center space-x-2">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                index <= currentStep
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {step.icon}
              <span className="hidden md:inline">{step.title}</span>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <Card className="border-border/50">
          <CardContent className="pt-6">
            {renderStep()}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
