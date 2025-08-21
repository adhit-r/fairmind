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
  Award,
  Trophy,
  TrendingUp,
  CheckCircle,
  Star,
  Play,
  ArrowRight,
  Eye,
  Zap,
  BarChart3,
  Users,
  Target
} from 'lucide-react'

export default function ExcelPage() {
  const router = useRouter()
  const [governanceScore, setGovernanceScore] = useState(87)
  const [achievements, setAchievements] = useState([
    { id: 'discovery', title: 'AI Landscape Assessment', completed: true, score: 92 },
    { id: 'assessment', title: 'Risk Assessment & Testing', completed: true, score: 88 },
    { id: 'security', title: 'Security Implementation', completed: true, score: 85 },
    { id: 'framework', title: 'Governance Framework', completed: true, score: 90 }
  ])

  const excellenceMetrics = [
    {
      id: 'bias-detection',
      title: 'Bias Detection Rate',
      value: '98.5%',
      target: '95%',
      status: 'excellent',
      icon: <Target className="h-6 w-6" />
    },
    {
      id: 'security-score',
      title: 'Security Score',
      value: '92/100',
      target: '85/100',
      status: 'excellent',
      icon: <TrendingUp className="h-6 w-6" />
    },
    {
      id: 'compliance-rate',
      title: 'Compliance Rate',
      value: '96.2%',
      target: '90%',
      status: 'excellent',
      icon: <CheckCircle className="h-6 w-6" />
    },
    {
      id: 'governance-maturity',
      title: 'Governance Maturity',
      value: 'Level 4',
      target: 'Level 3',
      status: 'excellent',
      icon: <Award className="h-6 w-6" />
    }
  ]

  const recommendations = [
    {
      title: 'Continuous Monitoring',
      description: 'Implement real-time monitoring for ongoing governance excellence',
      priority: 'high',
      impact: 'High'
    },
    {
      title: 'Advanced Analytics',
      description: 'Deploy advanced analytics for predictive governance insights',
      priority: 'medium',
      impact: 'Medium'
    },
    {
      title: 'Stakeholder Training',
      description: 'Conduct comprehensive training for all stakeholders',
      priority: 'medium',
      impact: 'High'
    }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          <Award className="h-8 w-8 inline mr-3" />
          Governance Excellence
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Achieve governance excellence with comprehensive progress tracking.
          Monitor performance and maintain continuous improvement.
        </NeoText>
      </div>

      {/* Overall Score */}
      <NeoCard className="text-center">
        <div className="mb-6">
          <h2 className="neo-heading neo-heading--lg mb-4">Overall Governance Score</h2>
          <div className="text-6xl font-bold text-blue-600 mb-2">{governanceScore}/100</div>
          <NeoText className="text-lg text-gray-600">Excellent Governance Maturity</NeoText>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
          <div 
            className="bg-gradient-to-r from-green-500 to-blue-500 h-4 rounded-full" 
            style={{ width: `${governanceScore}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm text-gray-600">
          <span>Level 1: Basic</span>
          <span>Level 2: Developing</span>
          <span>Level 3: Established</span>
          <span>Level 4: Excellent</span>
        </div>
      </NeoCard>

      {/* Excellence Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {excellenceMetrics.map((metric) => (
          <div key={metric.id} className="neo-card text-center">
            <div className="flex justify-center mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                {metric.icon}
              </div>
            </div>
            <h3 className="neo-heading neo-heading--md mb-2">{metric.title}</h3>
            <div className="text-2xl font-bold text-green-600 mb-1">{metric.value}</div>
            <NeoText className="text-sm text-gray-600">Target: {metric.target}</NeoText>
            <NeoBadge variant="success" className="mt-2">Exceeded</NeoBadge>
          </div>
        ))}
      </div>

      {/* Achievement Progress */}
      <NeoCard>
        <h2 className="neo-heading neo-heading--lg mb-6">Implementation Achievements</h2>
        <div className="space-y-4">
          {achievements.map((achievement) => (
            <div key={achievement.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <h3 className="neo-heading neo-heading--md">{achievement.title}</h3>
                  <NeoText className="text-sm text-gray-600">Completed successfully</NeoText>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-green-600">{achievement.score}/100</div>
                <NeoBadge variant="success">Completed</NeoBadge>
              </div>
            </div>
          ))}
        </div>
      </NeoCard>

      {/* Recommendations */}
      <NeoCard>
        <h2 className="neo-heading neo-heading--lg mb-6">Excellence Recommendations</h2>
        <div className="space-y-4">
          {recommendations.map((rec, index) => (
            <div key={index} className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${
                  rec.priority === 'high' ? 'bg-red-500' : 'bg-yellow-500'
                }`}>
                  {index + 1}
                </div>
              </div>
              <div className="flex-1">
                <h3 className="neo-heading neo-heading--md mb-1">{rec.title}</h3>
                <NeoText className="text-gray-600 mb-2">{rec.description}</NeoText>
                <div className="flex gap-2">
                  <NeoBadge variant={rec.priority === 'high' ? 'danger' : 'warning'}>
                    Priority: {rec.priority}
                  </NeoBadge>
                  <NeoBadge variant="info">Impact: {rec.impact}</NeoBadge>
                </div>
              </div>
              <NeoButton variant="secondary" size="sm">
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </NeoButton>
            </div>
          ))}
        </div>
      </NeoCard>

      {/* Excellence Dashboard */}
      <NeoCard>
        <h2 className="neo-heading neo-heading--lg mb-6">Governance Excellence Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
            <div className="text-3xl font-bold text-blue-600 mb-2">24/7</div>
            <NeoText className="font-semibold mb-1">Continuous Monitoring</NeoText>
            <NeoText className="text-sm text-gray-600">Real-time governance tracking</NeoText>
          </div>
          <div className="text-center p-6 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600 mb-2">100%</div>
            <NeoText className="font-semibold mb-1">Compliance Rate</NeoText>
            <NeoText className="text-sm text-gray-600">Regulatory adherence</NeoText>
          </div>
          <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
            <div className="text-3xl font-bold text-purple-600 mb-2">Level 4</div>
            <NeoText className="font-semibold mb-1">Maturity Level</NeoText>
            <NeoText className="text-sm text-gray-600">Governance excellence</NeoText>
          </div>
        </div>
      </NeoCard>

      {/* Action Buttons */}
      <div className="flex justify-center gap-4">
        <NeoButton variant="primary" size="lg">
          <BarChart3 className="h-5 w-5 mr-2" />
          View Detailed Analytics
        </NeoButton>
        <NeoButton variant="secondary" size="lg">
          <Users className="h-5 w-5 mr-2" />
          Generate Report
        </NeoButton>
      </div>

      {/* Excellence Guidelines */}
      <NeoAlert variant="info">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <NeoText variant="bold" className="mb-2">Excellence Guidelines</NeoText>
            <NeoText className="mb-2">• Maintain continuous monitoring and improvement processes</NeoText>
            <NeoText className="mb-2">• Regularly review and update governance frameworks</NeoText>
            <NeoText>• Engage stakeholders in ongoing governance excellence initiatives</NeoText>
          </div>
        </div>
      </NeoAlert>
    </div>
  )
}

