"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Input } from "@/components/ui/common/input"
import { Textarea } from "@/components/ui/common/textarea"
import { Badge } from "@/components/ui/common/badge"
import { Progress } from "@/components/ui/common/progress"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle, 
  Upload,
  Database,
  Shield,
  Users,
  Target,
  FileText,
  Building,
  Tag,
  BarChart3,
  Clock,
  CheckSquare,
  XCircle
} from "lucide-react"

interface OnboardingData {
  organization: {
    name: string
    industry: string
    size: string
    compliance_needs: string[]
  }
  useCases: {
    primary: string
    secondary: string[]
    ai_maturity: string
  }
  models: {
    count: number
    frameworks: string[]
    types: string[]
    files: File[]
  }
  security: {
    data_sensitivity: string
    compliance_frameworks: string[]
    security_level: string
  }
  team: {
    size: number
    roles: string[]
    expertise_level: string
  }
}

const steps = [
  {
    id: 'organization',
    title: 'Organization Setup',
    description: 'Tell us about your organization',
    icon: Building
  },
  {
    id: 'useCases',
    title: 'AI Use Cases',
    description: 'Define your AI governance needs',
    icon: Target
  },
  {
    id: 'models',
    title: 'Model Inventory',
    description: 'Upload and catalog your models',
    icon: Database
  },
  {
    id: 'security',
    title: 'Security & Compliance',
    description: 'Configure security requirements',
    icon: Shield
  },
  {
    id: 'team',
    title: 'Team Setup',
    description: 'Configure team access and roles',
    icon: Users
  },
  {
    id: 'review',
    title: 'Review & Complete',
    description: 'Review your configuration',
    icon: CheckSquare
  }
]

export function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [data, setData] = useState<OnboardingData>({
    organization: {
      name: '',
      industry: '',
      size: '',
      compliance_needs: []
    },
    useCases: {
      primary: '',
      secondary: [],
      ai_maturity: ''
    },
    models: {
      count: 0,
      frameworks: [],
      types: [],
      files: []
    },
    security: {
      data_sensitivity: '',
      compliance_frameworks: [],
      security_level: ''
    },
    team: {
      size: 0,
      roles: [],
      expertise_level: ''
    }
  })

  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploading, setUploading] = useState(false)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setData(prev => ({
      ...prev,
      models: {
        ...prev.models,
        files: [...prev.models.files, ...files]
      }
    }))
  }

  const removeFile = (index: number) => {
    setData(prev => ({
      ...prev,
      models: {
        ...prev.models,
        files: prev.models.files.filter((_, i) => i !== index)
      }
    }))
  }

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
    setUploading(true)
    
    // Simulate upload progress
    for (let i = 0; i <= 100; i += 10) {
      setUploadProgress(i)
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    setUploading(false)
    // Here you would typically save the onboarding data
    console.log('Onboarding completed:', data)
  }

  const progress = ((currentStep + 1) / steps.length) * 100

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Organization Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Organization Name</label>
                  <Input
                    value={data.organization.name}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      organization: { ...prev.organization, name: e.target.value }
                    }))}
                    placeholder="Enter organization name"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Industry</label>
                  <select
                    value={data.organization.industry}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      organization: { ...prev.organization, industry: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select industry</option>
                    <option value="technology">Technology</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="finance">Finance</option>
                    <option value="retail">Retail</option>
                    <option value="manufacturing">Manufacturing</option>
                    <option value="education">Education</option>
                    <option value="government">Government</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Company Size</label>
                  <select
                    value={data.organization.size}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      organization: { ...prev.organization, size: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select size</option>
                    <option value="startup">Startup (1-50)</option>
                    <option value="small">Small (51-200)</option>
                    <option value="medium">Medium (201-1000)</option>
                    <option value="large">Large (1000+)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Compliance Needs</label>
                  <div className="space-y-2 mt-2">
                    {['GDPR', 'HIPAA', 'SOX', 'PCI-DSS', 'ISO 27001'].map(compliance => (
                      <label key={compliance} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={data.organization.compliance_needs.includes(compliance)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setData(prev => ({
                                ...prev,
                                organization: {
                                  ...prev.organization,
                                  compliance_needs: [...prev.organization.compliance_needs, compliance]
                                }
                              }))
                            } else {
                              setData(prev => ({
                                ...prev,
                                organization: {
                                  ...prev.organization,
                                  compliance_needs: prev.organization.compliance_needs.filter(c => c !== compliance)
                                }
                              }))
                            }
                          }}
                          className="mr-2"
                        />
                        {compliance}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">AI Use Cases</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Primary AI Use Case</label>
                  <select
                    value={data.useCases.primary}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      useCases: { ...prev.useCases, primary: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select primary use case</option>
                    <option value="image-classification">Image Classification</option>
                    <option value="text-analysis">Text Analysis</option>
                    <option value="predictive-analytics">Predictive Analytics</option>
                    <option value="recommendation-systems">Recommendation Systems</option>
                    <option value="natural-language-processing">Natural Language Processing</option>
                    <option value="computer-vision">Computer Vision</option>
                    <option value="fraud-detection">Fraud Detection</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Secondary Use Cases</label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {['Image Classification', 'Text Analysis', 'Predictive Analytics', 'Recommendation Systems', 
                      'Natural Language Processing', 'Computer Vision', 'Fraud Detection'].map(useCase => (
                      <label key={useCase} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={data.useCases.secondary.includes(useCase)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setData(prev => ({
                                ...prev,
                                useCases: {
                                  ...prev.useCases,
                                  secondary: [...prev.useCases.secondary, useCase]
                                }
                              }))
                            } else {
                              setData(prev => ({
                                ...prev,
                                useCases: {
                                  ...prev.useCases,
                                  secondary: prev.useCases.secondary.filter(u => u !== useCase)
                                }
                              }))
                            }
                          }}
                          className="mr-2"
                        />
                        {useCase}
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">AI Maturity Level</label>
                  <select
                    value={data.useCases.ai_maturity}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      useCases: { ...prev.useCases, ai_maturity: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select maturity level</option>
                    <option value="beginner">Beginner - Exploring AI</option>
                    <option value="developing">Developing - Building first models</option>
                    <option value="mature">Mature - Production AI systems</option>
                    <option value="advanced">Advanced - AI-first organization</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4 neo-heading neo-heading--md">Model Inventory</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="text-sm font-medium neo-text neo-text--bold">Number of Models</label>
                  <Input
                    type="number"
                    value={data.models.count}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      models: { ...prev.models, count: parseInt(e.target.value) || 0 }
                    }))}
                    placeholder="0"
                    min="0"
                    className="neo-input"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium neo-text neo-text--bold">Primary Framework</label>
                  <select
                    value={data.models.frameworks[0] || ''}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      models: { 
                        ...prev.models, 
                        frameworks: e.target.value ? [e.target.value] : []
                      }
                    }))}
                    className="w-full px-3 py-2 border-2 border-black rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 neo-input"
                  >
                    <option value="">Select framework</option>
                    <option value="tensorflow">TensorFlow</option>
                    <option value="pytorch">PyTorch</option>
                    <option value="scikit-learn">Scikit-learn</option>
                    <option value="keras">Keras</option>
                    <option value="xgboost">XGBoost</option>
                    <option value="lightgbm">LightGBM</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="mb-6">
                <label className="text-sm font-medium neo-text neo-text--bold">Model Types</label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {['Classification', 'Regression', 'Clustering', 'NLP', 'Computer Vision', 'Recommendation', 'Anomaly Detection'].map(type => (
                    <label key={type} className="flex items-center neo-text">
                      <input
                        type="checkbox"
                        checked={data.models.types.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setData(prev => ({
                              ...prev,
                              models: {
                                ...prev.models,
                                types: [...prev.models.types, type]
                              }
                            }))
                          } else {
                            setData(prev => ({
                              ...prev,
                              models: {
                                ...prev.models,
                                types: prev.models.types.filter(t => t !== type)
                              }
                            }))
                          }
                        }}
                        className="mr-2 w-4 h-4 border-2 border-black rounded focus:ring-2 focus:ring-blue-500"
                      />
                      {type}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium neo-text neo-text--bold">Upload Model Files</label>
                <div className="border-4 border-dashed border-black rounded-lg p-8 text-center neo-card neo-card--lg">
                  <Upload className="h-16 w-16 mx-auto mb-4 text-gray-600" />
                  <p className="text-lg neo-text neo-text--bold mb-2">
                    Drag and drop your model files here, or click to browse
                  </p>
                  <p className="text-sm neo-text neo-text--muted mb-6">
                    Supported formats: .pkl, .pickle, .onnx, .h5, .hdf5, .pb, .pt, .pth
                  </p>
                  <Input
                    type="file"
                    multiple
                    accept=".pkl,.pickle,.onnx,.h5,.hdf5,.pb,.pt,.pth"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="model-upload"
                  />
                  <label htmlFor="model-upload" className="cursor-pointer">
                    <Button variant="outline" className="neo-button neo-button--primary neo-button--lg">
                      <Upload className="h-5 w-5 mr-2" />
                      Choose Model Files
                    </Button>
                  </label>
                </div>
              </div>

              {data.models.files.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium neo-text neo-text--bold">Uploaded Files:</h4>
                  {data.models.files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 border-2 border-black rounded-lg neo-card">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-gray-600" />
                        <div>
                          <p className="text-sm font-medium neo-text">{file.name}</p>
                          <p className="text-xs neo-text neo-text--muted">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => removeFile(index)}
                        className="neo-button neo-button--danger neo-button--sm"
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Model Upload Progress */}
              {data.models.files.length > 0 && (
                <div className="neo-card neo-card--md">
                  <div className="neo-card__header">
                    <h4 className="neo-heading neo-heading--sm">Upload Summary</h4>
                  </div>
                  <div className="neo-card__content">
                    <div className="space-y-2">
                      <div className="flex justify-between neo-text">
                        <span>Total files:</span>
                        <span className="neo-text--bold">{data.models.files.length}</span>
                      </div>
                      <div className="flex justify-between neo-text">
                        <span>Total size:</span>
                        <span className="neo-text--bold">
                          {(data.models.files.reduce((acc, file) => acc + file.size, 0) / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                      <div className="flex justify-between neo-text">
                        <span>Supported formats:</span>
                        <span className="neo-text--bold text-green-600">✓ All files</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Security & Compliance</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Data Sensitivity Level</label>
                  <select
                    value={data.security.data_sensitivity}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      security: { ...prev.security, data_sensitivity: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select sensitivity level</option>
                    <option value="public">Public - No restrictions</option>
                    <option value="internal">Internal - Company use only</option>
                    <option value="confidential">Confidential - Limited access</option>
                    <option value="restricted">Restricted - Highly sensitive</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">Security Level</label>
                  <select
                    value={data.security.security_level}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      security: { ...prev.security, security_level: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select security level</option>
                    <option value="basic">Basic - Standard security</option>
                    <option value="enhanced">Enhanced - Additional controls</option>
                    <option value="enterprise">Enterprise - Full security suite</option>
                    <option value="government">Government - Highest security</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">Compliance Frameworks</label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {['GDPR', 'HIPAA', 'SOX', 'PCI-DSS', 'ISO 27001', 'NIST', 'FedRAMP'].map(framework => (
                      <label key={framework} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={data.security.compliance_frameworks.includes(framework)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setData(prev => ({
                                ...prev,
                                security: {
                                  ...prev.security,
                                  compliance_frameworks: [...prev.security.compliance_frameworks, framework]
                                }
                              }))
                            } else {
                              setData(prev => ({
                                ...prev,
                                security: {
                                  ...prev.security,
                                  compliance_frameworks: prev.security.compliance_frameworks.filter(f => f !== framework)
                                }
                              }))
                            }
                          }}
                          className="mr-2"
                        />
                        {framework}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Team Setup</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Team Size</label>
                  <Input
                    type="number"
                    value={data.team.size}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      team: { ...prev.team, size: parseInt(e.target.value) || 0 }
                    }))}
                    placeholder="Number of team members"
                    min="1"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">Team Roles</label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {['Data Scientist', 'ML Engineer', 'DevOps Engineer', 'Security Engineer', 'Product Manager', 'Business Analyst', 'Legal/Compliance'].map(role => (
                      <label key={role} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={data.team.roles.includes(role)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setData(prev => ({
                                ...prev,
                                team: {
                                  ...prev.team,
                                  roles: [...prev.team.roles, role]
                                }
                              }))
                            } else {
                              setData(prev => ({
                                ...prev,
                                team: {
                                  ...prev.team,
                                  roles: prev.team.roles.filter(r => r !== role)
                                }
                              }))
                            }
                          }}
                          className="mr-2"
                        />
                        {role}
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">AI Expertise Level</label>
                  <select
                    value={data.team.expertise_level}
                    onChange={(e) => setData(prev => ({
                      ...prev,
                      team: { ...prev.team, expertise_level: e.target.value }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select expertise level</option>
                    <option value="beginner">Beginner - Learning AI</option>
                    <option value="intermediate">Intermediate - Some experience</option>
                    <option value="advanced">Advanced - Experienced practitioners</option>
                    <option value="expert">Expert - AI specialists</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Review Your Configuration</h3>
              
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Building className="h-5 w-5" />
                      Organization
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="font-medium">Name:</span> {data.organization.name}</div>
                      <div><span className="font-medium">Industry:</span> {data.organization.industry}</div>
                      <div><span className="font-medium">Size:</span> {data.organization.size}</div>
                      <div><span className="font-medium">Compliance:</span> {data.organization.compliance_needs.join(', ')}</div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      Use Cases
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Primary:</span> {data.useCases.primary}</div>
                      <div><span className="font-medium">Secondary:</span> {data.useCases.secondary.join(', ')}</div>
                      <div><span className="font-medium">Maturity:</span> {data.useCases.ai_maturity}</div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Database className="h-5 w-5" />
                      Models
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Count:</span> {data.models.count}</div>
                      <div><span className="font-medium">Framework:</span> {data.models.frameworks.join(', ')}</div>
                      <div><span className="font-medium">Types:</span> {data.models.types.join(', ')}</div>
                      <div><span className="font-medium">Files:</span> {data.models.files.length} uploaded</div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Security
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Data Sensitivity:</span> {data.security.data_sensitivity}</div>
                      <div><span className="font-medium">Security Level:</span> {data.security.security_level}</div>
                      <div><span className="font-medium">Compliance:</span> {data.security.compliance_frameworks.join(', ')}</div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Team
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Size:</span> {data.team.size} members</div>
                      <div><span className="font-medium">Roles:</span> {data.team.roles.join(', ')}</div>
                      <div><span className="font-medium">Expertise:</span> {data.team.expertise_level}</div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {uploading && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Setting up your workspace...</span>
                    <span className="text-sm text-gray-500">{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} />
                </div>
              )}
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Welcome to Fairmind</CardTitle>
              <CardDescription>
                Let's set up your AI governance workspace
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Step {currentStep + 1} of {steps.length}</div>
              <Progress value={progress} className="w-32" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {renderStep()}
            
            <div className="flex justify-between pt-6">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 0}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                Previous
              </Button>
              
              {currentStep === steps.length - 1 ? (
                <Button
                  onClick={handleComplete}
                  disabled={uploading}
                >
                  {uploading ? 'Setting up...' : (
                    <>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Complete Setup
                    </>
                  )}
                </Button>
              ) : (
                <Button onClick={handleNext}>
                  Next
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
