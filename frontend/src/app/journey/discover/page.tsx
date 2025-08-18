"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  NeoContainer,
  NeoGrid,
  NeoHeading,
  NeoText,
  NeoAlert,
  NeoCard,
  NeoButton,
  NeoBadge,
  NeoProgress
} from "@/components/ui/common/neo-components"
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
  AlertTriangle
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
      description: 'Tell us about your organization and AI usage'
    },
    {
      id: 2,
      title: 'AI Model Inventory',
      description: 'Identify your current AI models and use cases'
    },
    {
      id: 3,
      title: 'Compliance Requirements',
      description: 'Define your regulatory and compliance needs'
    },
    {
      id: 4,
      title: 'Risk Assessment',
      description: 'Evaluate your current risk exposure'
    }
  ]

  const organizationSizes = [
    { value: 'startup', label: 'Startup (1-50 employees)', description: 'Early-stage company with limited AI usage' },
    { value: 'sme', label: 'Small-Medium Enterprise (51-500)', description: 'Growing company with some AI implementations' },
    { value: 'enterprise', label: 'Enterprise (500+ employees)', description: 'Large organization with extensive AI usage' },
    { value: 'government', label: 'Government/Public Sector', description: 'Public sector with strict compliance requirements' }
  ]

  const useCaseOptions = [
    { id: 'customer-service', label: 'Customer Service & Chatbots', risk: 'medium' },
    { id: 'fraud-detection', label: 'Fraud Detection & Security', risk: 'high' },
    { id: 'recommendations', label: 'Recommendation Systems', risk: 'low' },
    { id: 'predictive-analytics', label: 'Predictive Analytics', risk: 'medium' },
    { id: 'computer-vision', label: 'Computer Vision & Image Processing', risk: 'high' },
    { id: 'nlp', label: 'Natural Language Processing', risk: 'medium' },
    { id: 'autonomous-systems', label: 'Autonomous Systems', risk: 'critical' },
    { id: 'financial-modeling', label: 'Financial Modeling & Trading', risk: 'high' }
  ]

  const complianceOptions = [
    { id: 'gdpr', label: 'GDPR (EU Data Protection)', required: true },
    { id: 'ccpa', label: 'CCPA (California Privacy)', required: false },
    { id: 'hipaa', label: 'HIPAA (Healthcare)', required: false },
    { id: 'sox', label: 'SOX (Financial Reporting)', required: false },
    { id: 'iso27001', label: 'ISO 27001 (Information Security)', required: false },
    { id: 'fedramp', label: 'FedRAMP (US Government)', required: false }
  ]

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    } else {
      // Complete discovery and move to next journey step
      router.push('/journey/assess')
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const updateDiscoveryData = (field: string, value: any) => {
    setDiscoveryData(prev => ({ ...prev, [field]: value }))
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <NeoHeading size="lg" className="mb-6">
              <Building className="h-6 w-6 inline mr-2" />
              Organization Overview
            </NeoHeading>
            
            <NeoCard>
              <h3 className="neo-heading neo-heading--md mb-4">Organization Size</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {organizationSizes.map((size) => (
                  <div
                    key={size.value}
                    className={`neo-card cursor-pointer transition-all duration-300 ${
                      discoveryData.organizationSize === size.value ? 'border-blue-500 border-4' : ''
                    }`}
                    onClick={() => updateDiscoveryData('organizationSize', size.value)}
                  >
                    <h4 className="neo-text neo-text--bold mb-2">{size.label}</h4>
                    <p className="neo-text text-sm text-gray-600">{size.description}</p>
                  </div>
                ))}
              </div>
            </NeoCard>

            <NeoCard>
              <h3 className="neo-heading neo-heading--md mb-4">AI Models Count</h3>
              <div className="flex items-center gap-4">
                <input
                  type="number"
                  min="0"
                  value={discoveryData.aiModels}
                  onChange={(e) => updateDiscoveryData('aiModels', parseInt(e.target.value) || 0)}
                  className="neo-text border-2 border-gray-300 rounded-lg px-4 py-2 w-32"
                  placeholder="0"
                />
                <NeoText>AI models in production or development</NeoText>
              </div>
            </NeoCard>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <NeoHeading size="lg" className="mb-6">
              <Brain className="h-6 w-6 inline mr-2" />
              AI Model Inventory
            </NeoHeading>
            
            <NeoCard>
              <h3 className="neo-heading neo-heading--md mb-4">AI Use Cases</h3>
              <p className="neo-text text-gray-600 mb-4">Select all the AI use cases that apply to your organization:</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {useCaseOptions.map((useCase) => (
                  <div
                    key={useCase.id}
                    className={`neo-card cursor-pointer transition-all duration-300 ${
                      discoveryData.useCases.includes(useCase.id) ? 'border-blue-500 border-4' : ''
                    }`}
                    onClick={() => {
                      const updated = discoveryData.useCases.includes(useCase.id)
                        ? discoveryData.useCases.filter(id => id !== useCase.id)
                        : [...discoveryData.useCases, useCase.id]
                      updateDiscoveryData('useCases', updated)
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="neo-text neo-text--bold">{useCase.label}</h4>
                      <NeoBadge variant={useCase.risk === 'critical' ? 'danger' : useCase.risk === 'high' ? 'warning' : 'info'}>
                        {useCase.risk}
                      </NeoBadge>
                    </div>
                    {discoveryData.useCases.includes(useCase.id) && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                ))}
              </div>
            </NeoCard>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <NeoHeading size="lg" className="mb-6">
              <FileText className="h-6 w-6 inline mr-2" />
              Compliance Requirements
            </NeoHeading>
            
            <NeoCard>
              <h3 className="neo-heading neo-heading--md mb-4">Regulatory Compliance</h3>
              <p className="neo-text text-gray-600 mb-4">Select the compliance frameworks that apply to your organization:</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {complianceOptions.map((compliance) => (
                  <div
                    key={compliance.id}
                    className={`neo-card cursor-pointer transition-all duration-300 ${
                      discoveryData.complianceNeeds.includes(compliance.id) ? 'border-blue-500 border-4' : ''
                    }`}
                    onClick={() => {
                      const updated = discoveryData.complianceNeeds.includes(compliance.id)
                        ? discoveryData.complianceNeeds.filter(id => id !== compliance.id)
                        : [...discoveryData.complianceNeeds, compliance.id]
                      updateDiscoveryData('complianceNeeds', updated)
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="neo-text neo-text--bold">{compliance.label}</h4>
                      {compliance.required && (
                        <NeoBadge variant="danger">Required</NeoBadge>
                      )}
                    </div>
                    {discoveryData.complianceNeeds.includes(compliance.id) && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                ))}
              </div>
            </NeoCard>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <NeoHeading size="lg" className="mb-6">
              <AlertTriangle className="h-6 w-6 inline mr-2" />
              Risk Assessment
            </NeoHeading>
            
            <NeoCard>
              <h3 className="neo-heading neo-heading--md mb-4">Current Risk Level</h3>
              <p className="neo-text text-gray-600 mb-4">Based on your AI usage, what's your current risk exposure?</p>
              
              <div className="space-y-4">
                {[
                  { value: 'low', label: 'Low Risk', description: 'Limited AI usage, low-impact applications', color: 'green' },
                  { value: 'medium', label: 'Medium Risk', description: 'Moderate AI usage, some high-impact areas', color: 'yellow' },
                  { value: 'high', label: 'High Risk', description: 'Extensive AI usage, critical applications', color: 'orange' },
                  { value: 'critical', label: 'Critical Risk', description: 'AI in safety-critical or regulated domains', color: 'red' }
                ].map((risk) => (
                  <div
                    key={risk.value}
                    className={`neo-card cursor-pointer transition-all duration-300 ${
                      discoveryData.riskLevel === risk.value ? 'border-blue-500 border-4' : ''
                    }`}
                    onClick={() => updateDiscoveryData('riskLevel', risk.value)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="neo-text neo-text--bold">{risk.label}</h4>
                        <p className="neo-text text-sm text-gray-600">{risk.description}</p>
                      </div>
                      <NeoBadge variant={risk.color as any}>{risk.label}</NeoBadge>
                    </div>
                  </div>
                ))}
              </div>
            </NeoCard>

            {/* Discovery Summary */}
            <NeoCard neo-card--info>
              <h3 className="neo-heading neo-heading--md mb-4">
                <Target className="h-5 w-5 inline mr-2" />
                Assessment Summary
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <NeoText className="font-bold">Organization:</NeoText>
                  <NeoText>{discoveryData.organizationSize || 'Not specified'}</NeoText>
                </div>
                <div>
                  <NeoText className="font-bold">AI Models:</NeoText>
                  <NeoText>{discoveryData.aiModels} models</NeoText>
                </div>
                <div>
                  <NeoText className="font-bold">Use Cases:</NeoText>
                  <NeoText>{discoveryData.useCases.length} selected</NeoText>
                </div>
                <div>
                  <NeoText className="font-bold">Compliance:</NeoText>
                  <NeoText>{discoveryData.complianceNeeds.length} frameworks</NeoText>
                </div>
              </div>
            </NeoCard>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          <Search className="h-8 w-8 inline mr-3" />
          AI Landscape Assessment
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Comprehensive analysis of your current AI infrastructure and governance requirements.
          This assessment will inform the development of a tailored governance strategy.
        </NeoText>
      </div>

      {/* Progress Bar */}
      <NeoCard>
        <div className="flex items-center justify-between mb-4">
          <NeoText className="font-bold">Step {currentStep} of 4</NeoText>
          <NeoText>{Math.round((currentStep / 4) * 100)}% Complete</NeoText>
        </div>
        <NeoProgress value={(currentStep / 4) * 100} variant="success" />
        
        <div className="flex justify-between mt-4 text-sm text-gray-600">
          {steps.map((step) => (
            <div key={step.id} className="text-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2 ${
                step.id <= currentStep ? 'bg-blue-500 text-white' : 'bg-gray-300'
              }`}>
                {step.id < currentStep ? <CheckCircle className="h-4 w-4" /> : step.id}
              </div>
              <NeoText className="text-xs">{step.title}</NeoText>
            </div>
          ))}
        </div>
      </NeoCard>

      {/* Step Content */}
      {renderStepContent()}

      {/* Navigation */}
      <div className="flex justify-between">
        <NeoButton
          variant="secondary"
          onClick={handleBack}
          disabled={currentStep === 1}
        >
          ← Back
        </NeoButton>
        
        <NeoButton
          variant="primary"
          onClick={handleNext}
        >
          {currentStep === 4 ? (
            <>
              Complete Discovery
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          ) : (
            <>
              Next Step
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          )}
        </NeoButton>
      </div>

      {/* Tips */}
      <NeoAlert variant="info">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <NeoText variant="bold" className="mb-2">Discovery Tips</NeoText>
            <NeoText className="mb-2">• Be honest about your current AI usage - this helps us provide better recommendations</NeoText>
            <NeoText className="mb-2">• Include all AI models, even those in development</NeoText>
            <NeoText>• Don't worry if you're unsure about compliance - we'll help you identify requirements</NeoText>
          </div>
        </div>
      </NeoAlert>
    </div>
  )
}
