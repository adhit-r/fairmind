"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Compass,
  Brain,
  Database,
  Users,
  Target,
  ArrowRight,
  CheckCircle,
  Upload,
  Eye,
  BarChart3,
  Shield,
  Zap,
  Search,
  Building,
  TestTube,
  FileText,
  AlertTriangle,
  ArrowLeft,
  Play,
  Clock,
  Settings,
  Globe,
  Lock,
  Scale
} from 'lucide-react'

export default function DiscoverPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [discoveryData, setDiscoveryData] = useState({
    organizationSize: '',
    aiModels: 0,
    useCases: [] as string[],
    complianceNeeds: [] as string[],
    riskLevel: 'medium'
  })

  const steps = [
    {
      id: 1,
      title: 'Organization Overview',
      description: 'Tell us about your organization and AI usage',
      icon: Building
    },
    {
      id: 2,
      title: 'AI Model Inventory',
      description: 'Identify your current AI models and use cases',
      icon: Brain
    },
    {
      id: 3,
      title: 'Compliance Requirements',
      description: 'Define your regulatory and compliance needs',
      icon: Shield
    },
    {
      id: 4,
      title: 'Risk Assessment',
      description: 'Evaluate your current risk exposure',
      icon: AlertTriangle
    }
  ]

  const organizationSizes = [
    { value: 'startup', label: 'Startup (1-50 employees)', description: 'Early-stage company with limited AI usage', icon: Zap },
    { value: 'sme', label: 'Small-Medium Enterprise (51-500)', description: 'Growing company with some AI implementations', icon: Users },
    { value: 'enterprise', label: 'Enterprise (500+ employees)', description: 'Large organization with extensive AI usage', icon: Building },
    { value: 'government', label: 'Government/Public Sector', description: 'Public sector with strict compliance requirements', icon: Globe }
  ]

  const useCaseOptions = [
    { id: 'customer-service', label: 'Customer Service & Chatbots', risk: 'medium', icon: Users },
    { id: 'fraud-detection', label: 'Fraud Detection & Security', risk: 'high', icon: Shield },
    { id: 'recommendations', label: 'Recommendation Systems', risk: 'low', icon: Target },
    { id: 'predictive-analytics', label: 'Predictive Analytics', risk: 'medium', icon: BarChart3 },
    { id: 'computer-vision', label: 'Computer Vision & Image Processing', risk: 'high', icon: Eye },
    { id: 'nlp', label: 'Natural Language Processing', risk: 'medium', icon: FileText },
    { id: 'autonomous-systems', label: 'Autonomous Systems', risk: 'critical', icon: Settings },
    { id: 'financial-modeling', label: 'Financial Modeling & Trading', risk: 'high', icon: Scale }
  ]

  const complianceOptions = [
    { id: 'gdpr', label: 'GDPR (EU Data Protection)', required: true, icon: Lock },
    { id: 'ccpa', label: 'CCPA (California Privacy)', required: false, icon: Shield },
    { id: 'hipaa', label: 'HIPAA (Healthcare)', required: false, icon: Users },
    { id: 'sox', label: 'SOX (Financial Reporting)', required: false, icon: FileText },
    { id: 'iso27001', label: 'ISO 27001 (Information Security)', required: false, icon: Lock },
    { id: 'fedramp', label: 'FedRAMP (US Government)', required: false, icon: Globe }
  ]

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    } else {
      // Complete discovery and move to next phase
      router.push('/journey/assess')
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    } else {
      router.push('/')
    }
  }

  const handleOrganizationSelect = (size: string) => {
    setDiscoveryData(prev => ({ ...prev, organizationSize: size }))
  }

  const handleUseCaseToggle = (useCase: string) => {
    setDiscoveryData(prev => ({
      ...prev,
      useCases: prev.useCases.includes(useCase)
        ? prev.useCases.filter(c => c !== useCase)
        : [...prev.useCases, useCase]
    }))
  }

  const handleComplianceToggle = (compliance: string) => {
    setDiscoveryData(prev => ({
      ...prev,
      complianceNeeds: prev.complianceNeeds.includes(compliance)
        ? prev.complianceNeeds.filter(c => c !== compliance)
        : [...prev.complianceNeeds, compliance]
    }))
  }

  const handleRiskLevelSelect = (level: string) => {
    setDiscoveryData(prev => ({ ...prev, riskLevel: level }))
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-100 text-green-800 border-green-300'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'critical': return 'bg-red-100 text-red-800 border-red-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-black text-gray-900 mb-4">Organization Overview</h2>
              <p className="text-lg font-bold text-gray-600">Help us understand your organization's AI governance needs</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {organizationSizes.map((size) => (
                <div
                  key={size.value}
                  onClick={() => handleOrganizationSelect(size.value)}
                  className={`p-6 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    discoveryData.organizationSize === size.value
                      ? 'border-blue-500 bg-blue-50 shadow-4px-4px-0px-black'
                      : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-black'
                  }`}
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <size.icon className="h-5 w-5 text-blue-600" />
                    </div>
                    <h3 className="font-black text-gray-900">{size.label}</h3>
                  </div>
                  <p className="text-sm font-bold text-gray-600">{size.description}</p>
                </div>
              ))}
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-black text-gray-900 mb-4">AI Model Inventory</h2>
              <p className="text-lg font-bold text-gray-600">Select the AI use cases that apply to your organization</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {useCaseOptions.map((useCase) => (
                <div
                  key={useCase.id}
                  onClick={() => handleUseCaseToggle(useCase.id)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    discoveryData.useCases.includes(useCase.id)
                      ? 'border-green-500 bg-green-50 shadow-4px-4px-0px-black'
                      : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-black'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        <useCase.icon className="h-4 w-4 text-gray-600" />
                      </div>
                      <span className="font-black text-gray-900">{useCase.label}</span>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-bold border ${getRiskColor(useCase.risk)}`}>
                      {useCase.risk.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-black text-gray-900 mb-4">Compliance Requirements</h2>
              <p className="text-lg font-bold text-gray-600">Select the regulatory frameworks that apply to your organization</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {complianceOptions.map((compliance) => (
                <div
                  key={compliance.id}
                  onClick={() => handleComplianceToggle(compliance.id)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    discoveryData.complianceNeeds.includes(compliance.id)
                      ? 'border-purple-500 bg-purple-50 shadow-4px-4px-0px-black'
                      : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-black'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <compliance.icon className="h-4 w-4 text-purple-600" />
                      </div>
                      <span className="font-black text-gray-900">{compliance.label}</span>
                    </div>
                    {compliance.required && (
                      <span className="px-2 py-1 bg-red-100 text-red-800 border border-red-300 rounded text-xs font-bold">
                        REQUIRED
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-black text-gray-900 mb-4">Risk Assessment</h2>
              <p className="text-lg font-bold text-gray-600">Evaluate your current AI risk exposure level</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { value: 'low', label: 'Low Risk', description: 'Limited AI usage, basic governance needs', color: 'green' },
                { value: 'medium', label: 'Medium Risk', description: 'Moderate AI usage, standard governance', color: 'yellow' },
                { value: 'high', label: 'High Risk', description: 'Extensive AI usage, advanced governance', color: 'orange' },
                { value: 'critical', label: 'Critical Risk', description: 'Sensitive AI applications, strict governance', color: 'red' }
              ].map((risk) => (
                <div
                  key={risk.value}
                  onClick={() => handleRiskLevelSelect(risk.value)}
                  className={`p-6 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    discoveryData.riskLevel === risk.value
                      ? `border-${risk.color}-500 bg-${risk.color}-50 shadow-4px-4px-0px-black`
                      : 'border-gray-300 bg-white hover:border-gray-400 shadow-2px-2px-0px-black'
                  }`}
                >
                  <h3 className="font-black text-gray-900 mb-2">{risk.label}</h3>
                  <p className="text-sm font-bold text-gray-600">{risk.description}</p>
                </div>
              ))}
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-black text-gray-900 mb-4 flex items-center justify-center">
          <Search className="h-8 w-8 mr-3 text-blue-600" />
          AI Landscape Assessment
        </h1>
        <p className="text-lg font-bold text-gray-600 max-w-2xl mx-auto">
          Comprehensive analysis of your current AI infrastructure and governance requirements.
          This assessment will inform the development of a tailored governance strategy.
        </p>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between mb-4">
          <div className="font-black text-gray-900">Step {currentStep} of 4</div>
          <div className="font-black text-gray-900">{Math.round((currentStep / 4) * 100)}% Complete</div>
        </div>
        
        <div className="w-full bg-gray-200 border border-black rounded-full h-4 mb-4">
          <div 
            className="bg-gradient-to-r from-blue-500 to-green-500 h-4 rounded-full border border-black transition-all duration-500"
            style={{ width: `${(currentStep / 4) * 100}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm font-bold text-gray-600">
          {steps.map((step) => (
            <div key={step.id} className="text-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2 border-2 ${
                step.id <= currentStep ? 'bg-blue-500 text-white border-black' : 'bg-gray-300 border-gray-300'
              }`}>
                {step.id < currentStep ? <CheckCircle className="h-4 w-4" /> : step.id}
              </div>
              <div className="text-xs font-bold">{step.title}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          className="bg-gray-100 text-gray-700 border-2 border-gray-300 px-6 py-3 rounded-lg font-bold hover:bg-gray-200 shadow-2px-2px-0px-black transition-all duration-200"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          {currentStep === 1 ? 'Back to Dashboard' : 'Previous'}
        </button>
        
        <button
          onClick={handleNext}
          disabled={!discoveryData.organizationSize || discoveryData.useCases.length === 0}
          className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {currentStep === 4 ? (
            <>
              <Play className="h-4 w-4 mr-2" />
              Complete Assessment
            </>
          ) : (
            <>
              Next Step
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          )}
        </button>
      </div>
    </div>
  )
}
