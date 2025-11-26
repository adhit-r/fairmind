'use client'

import React, { useState, useRef, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import * as AlertDialog from '@radix-ui/react-alert-dialog'
import {
  Send,
  Loader2,
  Sparkles,
  MessageCircle,
  AlertCircle,
  CheckCircle,
  Copy,
  Trash2,
} from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface GapAnalysisResult {
  gap_id: string
  control_name: string
  severity: string
  analysis: string
  recommendations: string[]
}

interface RemediationPlan {
  plan_id: string
  title: string
  steps: Array<{
    step_number: number
    description: string
    effort_level: string
    estimated_days: number
  }>
  total_effort_days: number
}

interface AIComplianceAssistantProps {
  systemId: string
  framework: string
  onGapAnalysis?: (analysis: GapAnalysisResult[]) => void
  onRemediationPlan?: (plan: RemediationPlan) => void
}

export const AIComplianceAssistant: React.FC<AIComplianceAssistantProps> = ({
  systemId,
  framework,
  onGapAnalysis,
  onRemediationPlan,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        'Hello! I\'m your AI Compliance Assistant. I can help you with compliance questions, gap analysis, and remediation planning. What would you like to know about your compliance status?',
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [gapAnalysisResults, setGapAnalysisResults] = useState<GapAnalysisResult[]>([])
  const [remediationPlan, setRemediationPlan] = useState<RemediationPlan | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [clearDialogOpen, setClearDialogOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Simulate AI response - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateMockResponse(inputValue, framework),
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Failed to get response:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const generateMockResponse = (query: string, framework: string): string => {
    const lowerQuery = query.toLowerCase()

    if (lowerQuery.includes('gap') || lowerQuery.includes('missing')) {
      return `Based on your ${framework} compliance status, I've identified the following gaps:

1. **Data Localization Control** - Critical
   - Your system is storing some personal data outside India
   - DPDP Act Section 16 requires sensitive personal data to be stored in India
   - Recommendation: Migrate data to India-based servers

2. **Consent Management** - High
   - Consent records lack withdrawal mechanism
   - DPDP Act Section 6 requires explicit withdrawal capability
   - Recommendation: Implement consent withdrawal UI

3. **Language Support** - Medium
   - System only supports English and Hindi
   - NITI Aayog principles require support for regional languages
   - Recommendation: Add support for Tamil, Telugu, Bengali, Marathi

Would you like me to generate a detailed remediation plan for these gaps?`
    }

    if (lowerQuery.includes('remediation') || lowerQuery.includes('fix')) {
      return `I'll create a comprehensive remediation plan for your compliance gaps.

**Remediation Plan Summary:**
- Total Estimated Effort: 45 days
- Priority: Address critical gaps first (10 days)
- Then high-priority gaps (20 days)
- Finally medium-priority gaps (15 days)

**Phase 1: Critical Gaps (10 days)**
1. Data Migration to India (8 days) - High effort
2. Backup and Disaster Recovery Setup (2 days) - Medium effort

**Phase 2: High Priority (20 days)**
1. Consent Management System (12 days) - High effort
2. Consent Withdrawal Mechanism (5 days) - Medium effort
3. Testing and Validation (3 days) - Low effort

**Phase 3: Medium Priority (15 days)**
1. Language Support Implementation (10 days) - High effort
2. Regional Language Testing (5 days) - Medium effort

Would you like me to elaborate on any specific phase?`
    }

    if (lowerQuery.includes('dpdp') || lowerQuery.includes('data protection')) {
      return `The Digital Personal Data Protection (DPDP) Act 2023 is India's primary data protection law. Key requirements include:

**Consent Management (Section 6)**
- Explicit, informed consent required for data processing
- Consent must specify purpose, duration, and data categories
- Users must have right to withdraw consent

**Data Localization (Section 16)**
- Sensitive personal data must be stored in India
- Non-sensitive data can be transferred with restrictions
- Cross-border transfers require compliance with approved countries

**Data Principal Rights (Section 8)**
- Right to access personal data
- Right to correction and erasure
- Right to grievance redressal

**Security Obligations (Section 7)**
- Implement reasonable security measures
- Notify Data Protection Board of breaches
- Maintain audit logs

Would you like specific guidance on any of these requirements?`
    }

    return `Thank you for your question about ${framework} compliance. Based on your system configuration, here are some insights:

Your current compliance score is 75%, with 15 out of 20 requirements met. The main areas for improvement are:
- Data localization verification
- Consent management mechanisms
- Language support for regional languages

I can help you with:
1. **Gap Analysis** - Identify specific compliance gaps
2. **Remediation Planning** - Create step-by-step remediation plans
3. **Compliance Q&A** - Answer questions about Indian regulations
4. **Policy Generation** - Generate compliant policies and documents

What would you like to focus on?`
  }

  const handleGapAnalysis = async () => {
    setIsLoading(true)
    try {
      // Simulate gap analysis
      await new Promise(resolve => setTimeout(resolve, 1500))

      const mockResults: GapAnalysisResult[] = [
        {
          gap_id: 'GAP_001',
          control_name: 'Data Localization',
          severity: 'critical',
          analysis:
            'System is storing sensitive personal data in multiple geographic locations outside India, violating DPDP Act Section 16.',
          recommendations: [
            'Migrate all sensitive personal data to India-based data centers',
            'Implement data residency checks',
            'Set up automated compliance monitoring',
          ],
        },
        {
          gap_id: 'GAP_002',
          control_name: 'Consent Management',
          severity: 'high',
          analysis:
            'Current consent mechanism lacks withdrawal capability required by DPDP Act Section 6.',
          recommendations: [
            'Implement consent withdrawal UI',
            'Add consent audit logging',
            'Create consent revocation workflow',
          ],
        },
      ]

      setGapAnalysisResults(mockResults)
      onGapAnalysis?.(mockResults)

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I've completed the gap analysis for your ${framework} compliance. I found ${mockResults.length} significant gaps that need attention. The results are displayed in the "Gap Analysis" tab.`,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Gap analysis failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemediationPlan = async () => {
    setIsLoading(true)
    try {
      // Simulate remediation plan generation
      await new Promise(resolve => setTimeout(resolve, 1500))

      const mockPlan: RemediationPlan = {
        plan_id: 'PLAN_001',
        title: 'India Compliance Remediation Plan',
        steps: [
          {
            step_number: 1,
            description: 'Migrate sensitive personal data to India-based servers',
            effort_level: 'high',
            estimated_days: 8,
          },
          {
            step_number: 2,
            description: 'Implement consent withdrawal mechanism',
            effort_level: 'medium',
            estimated_days: 5,
          },
          {
            step_number: 3,
            description: 'Add support for regional Indian languages',
            effort_level: 'high',
            estimated_days: 10,
          },
          {
            step_number: 4,
            description: 'Set up compliance monitoring and alerting',
            effort_level: 'medium',
            estimated_days: 4,
          },
        ],
        total_effort_days: 27,
      }

      setRemediationPlan(mockPlan)
      onRemediationPlan?.(mockPlan)

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I've generated a comprehensive remediation plan with ${mockPlan.steps.length} steps and an estimated effort of ${mockPlan.total_effort_days} days. Check the "Remediation Plan" tab for details.`,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Remediation plan generation failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content:
          'Hello! I\'m your AI Compliance Assistant. I can help you with compliance questions, gap analysis, and remediation planning. What would you like to know about your compliance status?',
        timestamp: new Date(),
      },
    ])
    setClearDialogOpen(false)
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="chat" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="chat" className="gap-2">
            <MessageCircle className="h-4 w-4" />
            Chat
          </TabsTrigger>
          <TabsTrigger value="gaps" className="gap-2">
            <AlertCircle className="h-4 w-4" />
            Gap Analysis
          </TabsTrigger>
          <TabsTrigger value="remediation" className="gap-2">
            <CheckCircle className="h-4 w-4" />
            Remediation Plan
          </TabsTrigger>
        </TabsList>

        {/* Chat Tab */}
        <TabsContent value="chat" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI Compliance Assistant
              </CardTitle>
              <CardDescription>
                Ask questions about {framework} compliance and get AI-powered insights
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Messages */}
              <div className="h-96 overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-lg border">
                {messages.map(message => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-800 border border-gray-200'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p
                        className={`text-xs mt-1 ${
                          message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white text-gray-800 border border-gray-200 px-4 py-2 rounded-lg">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="flex gap-2">
                <Input
                  placeholder="Ask about compliance requirements..."
                  value={inputValue}
                  onChange={e => setInputValue(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && handleSendMessage()}
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputValue.trim()}
                  className="gap-2"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {/* Quick Actions */}
              <div className="grid grid-cols-2 gap-2 pt-2">
                <Button
                  variant="noShadow"
                  size="sm"
                  onClick={handleGapAnalysis}
                  disabled={isLoading}
                  className="gap-2"
                >
                  <AlertCircle className="h-4 w-4" />
                  Analyze Gaps
                </Button>
                <Button
                  variant="noShadow"
                  size="sm"
                  onClick={handleRemediationPlan}
                  disabled={isLoading}
                  className="gap-2"
                >
                  <CheckCircle className="h-4 w-4" />
                  Generate Plan
                </Button>
              </div>

              {/* Clear Chat */}
              <div className="flex justify-end pt-2">
                <AlertDialog.Root open={clearDialogOpen} onOpenChange={setClearDialogOpen}>
                  <AlertDialog.Trigger asChild>
                    <Button
                      variant="noShadow"
                      size="sm"
                      onClick={() => setClearDialogOpen(true)}
                      className="text-red-600 gap-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      Clear Chat
                    </Button>
                  </AlertDialog.Trigger>
                  <AlertDialog.Portal>
                    <AlertDialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
                    <AlertDialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-sm translate-x-[-50%] translate-y-[-50%] rounded-lg border bg-white p-6 shadow-lg">
                      <AlertDialog.Title className="font-semibold">Clear Chat History?</AlertDialog.Title>
                      <AlertDialog.Description className="mt-2 text-sm text-gray-600">
                        This will clear all messages from the conversation.
                      </AlertDialog.Description>
                      <div className="mt-6 flex gap-2 justify-end">
                        <AlertDialog.Cancel asChild>
                          <Button variant="noShadow" size="sm">Cancel</Button>
                        </AlertDialog.Cancel>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={clearChat}
                        >
                          Clear
                        </Button>
                      </div>
                    </AlertDialog.Content>
                  </AlertDialog.Portal>
                </AlertDialog.Root>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Gap Analysis Tab */}
        <TabsContent value="gaps">
          <Card>
            <CardHeader>
              <CardTitle>Gap Analysis Results</CardTitle>
              <CardDescription>
                AI-identified compliance gaps and recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              {gapAnalysisResults.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No gap analysis results yet</p>
                  <p className="text-sm text-gray-400">Click "Analyze Gaps" in the chat to generate results</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {gapAnalysisResults.map(gap => (
                    <div key={gap.gap_id} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-start justify-between">
                        <h4 className="font-semibold">{gap.control_name}</h4>
                        <Badge
                          className={
                            gap.severity === 'critical'
                              ? 'bg-red-100 text-red-800'
                              : gap.severity === 'high'
                                ? 'bg-orange-100 text-orange-800'
                                : 'bg-yellow-100 text-yellow-800'
                          }
                        >
                          {gap.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-700">{gap.analysis}</p>
                      <div>
                        <p className="text-sm font-medium mb-2">Recommendations:</p>
                        <ul className="space-y-1">
                          {gap.recommendations.map((rec, idx) => (
                            <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                              <span className="text-blue-500 mt-1">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <Button
                        variant="noShadow"
                        size="sm"
                        onClick={() => copyToClipboard(gap.analysis, gap.gap_id)}
                        className="gap-2"
                      >
                        {copiedId === gap.gap_id ? (
                          <>
                            <CheckCircle className="h-4 w-4" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" />
                            Copy
                          </>
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Remediation Plan Tab */}
        <TabsContent value="remediation">
          <Card>
            <CardHeader>
              <CardTitle>Remediation Plan</CardTitle>
              <CardDescription>Step-by-step plan to address compliance gaps</CardDescription>
            </CardHeader>
            <CardContent>
              {!remediationPlan ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No remediation plan generated yet</p>
                  <p className="text-sm text-gray-400">
                    Click "Generate Plan" in the chat to create a plan
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-gray-600">Total Estimated Effort</p>
                    <p className="text-2xl font-bold text-blue-600">{remediationPlan.total_effort_days} days</p>
                  </div>

                  <div className="space-y-3">
                    {remediationPlan.steps.map(step => (
                      <div
                        key={step.step_number}
                        className={`p-4 rounded-lg border-l-4 ${
                          step.effort_level === 'high'
                            ? 'border-l-red-500 bg-red-50'
                            : step.effort_level === 'medium'
                              ? 'border-l-yellow-500 bg-yellow-50'
                              : 'border-l-green-500 bg-green-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-sm">
                              Step {step.step_number}: {step.description}
                            </h4>
                            <p className="text-xs text-gray-600 mt-1">
                              Estimated effort: {step.estimated_days} day
                              {step.estimated_days !== 1 ? 's' : ''}
                            </p>
                          </div>
                          <Badge
                            className={
                              step.effort_level === 'high'
                                ? 'bg-red-100 text-red-800'
                                : step.effort_level === 'medium'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-green-100 text-green-800'
                            }
                          >
                            {step.effort_level.toUpperCase()}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AIComplianceAssistant
