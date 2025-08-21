"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Button } from "@/components/ui/common/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Badge } from "@/components/ui/common/badge"
import { 
  CheckCircle, 
  Upload,
  Database,
  Shield,
  Users,
  Target,
  FileText,
  Building,
  ArrowRight,
  Zap,
  BarChart3
} from "lucide-react"

export default function OnboardingPage() {
  const router = useRouter()
  const { user, updateProfile } = useAuth()
  const [currentStep, setCurrentStep] = useState(1)
  const [loading, setLoading] = useState(false)

  const steps = [
    {
      id: 1,
      title: 'Welcome to Fairmind',
      description: 'Let\'s get your organization set up for AI governance',
      icon: Building
    },
    {
      id: 2,
      title: 'Upload Your First Model',
      description: 'Start by uploading a model to analyze for bias and security',
      icon: Upload
    },
    {
      id: 3,
      title: 'Run Your First Analysis',
      description: 'Test our bias detection and security analysis features',
      icon: Shield
    },
    {
      id: 4,
      title: 'Complete Setup',
      description: 'You\'re all set! Explore the platform',
      icon: CheckCircle
    }
  ]

  const handleCompleteOnboarding = async () => {
    setLoading(true)
    try {
      await updateProfile({ onboarding_completed: true })
      router.push('/dashboard')
    } catch (error) {
      console.error('Error completing onboarding:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSkipToDashboard = () => {
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Fairmind
          </h1>
          <p className="text-lg text-gray-600">
            AI Governance Platform for {user?.organization_name}
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <div className="flex space-x-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  currentStep >= step.id 
                    ? 'bg-blue-600 border-blue-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-500'
                }`}>
                  {currentStep > step.id ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <step.icon className="h-5 w-5" />
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-0.5 mx-2 ${
                    currentStep > step.id ? 'bg-blue-600' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <steps[currentStep - 1].icon className="h-6 w-6" />
              {steps[currentStep - 1].title}
            </CardTitle>
            <CardDescription>
              {steps[currentStep - 1].description}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Database className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                    <h3 className="font-medium">Model Registry</h3>
                    <p className="text-sm text-gray-600">Upload and manage your AI models</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Shield className="h-8 w-8 mx-auto mb-2 text-green-600" />
                    <h3 className="font-medium">Bias Detection</h3>
                    <p className="text-sm text-gray-600">Analyze models for fairness and bias</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <Target className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                    <h3 className="font-medium">Security Testing</h3>
                    <p className="text-sm text-gray-600">Test models for security vulnerabilities</p>
                  </div>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">What you can do:</h3>
                  <ul className="space-y-1 text-sm text-gray-700">
                    <li>• Upload and catalog your AI models</li>
                    <li>• Run comprehensive bias analysis</li>
                    <li>• Test for security vulnerabilities</li>
                    <li>• Generate compliance reports</li>
                    <li>• Monitor model performance</li>
                  </ul>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="text-center p-8 border-2 border-dashed border-gray-300 rounded-lg">
                  <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Upload Your First Model</h3>
                  <p className="text-gray-600 mb-4">
                    Supported formats: .pkl, .joblib, .h5, .onnx, .pb, .pt, .pth
                  </p>
                  <Button variant="outline" size="lg">
                    Choose Model File
                  </Button>
                </div>
                
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Demo Models Available:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Demo</Badge>
                      <span>Credit Risk Model</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Demo</Badge>
                      <span>Fraud Detection Model</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Demo</Badge>
                      <span>Loan Approval Model</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Demo</Badge>
                      <span>Hiring Assistant Model</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Bias Detection
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 mb-3">
                        Analyze your models for fairness and bias across different demographic groups.
                      </p>
                      <Button className="w-full">
                        Run Bias Analysis
                      </Button>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Target className="h-5 w-5" />
                        Security Testing
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 mb-3">
                        Test your models for security vulnerabilities and compliance issues.
                      </p>
                      <Button className="w-full">
                        Run Security Test
                      </Button>
                    </CardContent>
                  </Card>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Analysis Features:</h3>
                  <ul className="space-y-1 text-sm text-gray-700">
                    <li>• Statistical parity and equal opportunity analysis</li>
                    <li>• Intersectional bias detection</li>
                    <li>• SHAP and LIME explainability</li>
                    <li>• OWASP AI/LLM security testing</li>
                    <li>• Compliance reporting</li>
                  </ul>
                </div>
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-6">
                <div className="text-center">
                  <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-600" />
                  <h3 className="text-xl font-medium mb-2">Setup Complete!</h3>
                  <p className="text-gray-600">
                    Your organization is ready to start managing AI governance.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4">
                    <Database className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                    <h4 className="font-medium">Model Registry</h4>
                    <p className="text-sm text-gray-600">Manage your AI models</p>
                  </div>
                  <div className="text-center p-4">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 text-green-600" />
                    <h4 className="font-medium">Dashboard</h4>
                    <p className="text-sm text-gray-600">View analytics and reports</p>
                  </div>
                  <div className="text-center p-4">
                    <FileText className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                    <h4 className="font-medium">Documentation</h4>
                    <p className="text-sm text-gray-600">Learn how to use the platform</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
          >
            Previous
          </Button>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleSkipToDashboard}
            >
              Skip to Dashboard
            </Button>
            
            {currentStep < steps.length ? (
              <Button
                onClick={() => setCurrentStep(currentStep + 1)}
              >
                Next
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleCompleteOnboarding}
                disabled={loading}
              >
                {loading ? "Completing..." : "Get Started"}
                <Zap className="h-4 w-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
