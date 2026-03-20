/**
 * Bias Detection Widget for Compliance Dashboard
 * Displays latest LLM bias evaluation summary with risk indicator
 */

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { IconBrain, IconArrowRight, IconFlame, IconAlertTriangle, IconCheck } from '@tabler/icons-react'

interface BiasDetectionData {
  timestamp: string
  modelType: string
  overallRisk: 'low' | 'medium' | 'high' | 'critical'
  biasRate: number
  testsPassed: number
  totalTests: number
  complianceScore: number
  latestRecommendations: string[]
}

const mockBiasData: BiasDetectionData = {
  timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  modelType: 'llm',
  overallRisk: 'medium',
  biasRate: 0.42,
  testsPassed: 4,
  totalTests: 6,
  complianceScore: 0.68,
  latestRecommendations: [
    'Implement debiasing techniques during training',
    'Expand training data to include underrepresented groups',
  ],
}

export function BiasDetectionWidget() {
  const [biasData, setBiasData] = useState<BiasDetectionData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // In production, this would fetch from /api/v1/modern-bias/detection-results
    // For now, use mock data after a short delay
    const timer = setTimeout(() => {
      setBiasData(mockBiasData)
      setIsLoading(false)
    }, 500)

    return () => clearTimeout(timer)
  }, [])

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'low':
        return <IconCheck className="h-4 w-4" />
      case 'medium':
        return <IconAlertTriangle className="h-4 w-4" />
      case 'high':
        return <IconFlame className="h-4 w-4" />
      case 'critical':
        return <IconFlame className="h-4 w-4" />
      default:
        return null
    }
  }

  const lastEvaluationDate = biasData
    ? new Date(biasData.timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Never'

  return (
    <Card className="border-2 border-black shadow-brutal">
      <CardHeader className="border-b-2 border-black">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 border-2 border-black">
              <IconBrain className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <CardTitle className="flex items-center gap-2">
                LLM Bias Detection
              </CardTitle>
              <CardDescription>Latest evaluation summary</CardDescription>
            </div>
          </div>
          {biasData && (
            <Badge className={`border-2 border-current font-bold ${getRiskColor(biasData.overallRisk)}`}>
              <div className="flex items-center gap-1">
                {getRiskIcon(biasData.overallRisk)}
                {biasData.overallRisk.toUpperCase()}
              </div>
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {isLoading ? (
          <div className="h-40 flex items-center justify-center text-muted-foreground">
            <div className="animate-pulse">Loading bias detection data...</div>
          </div>
        ) : biasData ? (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="border-2 border-black p-3 bg-gray-50">
                <p className="text-xs text-muted-foreground font-bold">BIAS RATE</p>
                <p className="text-2xl font-bold mt-1">{(biasData.biasRate * 100).toFixed(1)}%</p>
              </div>
              <div className="border-2 border-black p-3 bg-gray-50">
                <p className="text-xs text-muted-foreground font-bold">TESTS PASSED</p>
                <p className="text-2xl font-bold mt-1">
                  {biasData.testsPassed}/{biasData.totalTests}
                </p>
              </div>
              <div className="border-2 border-black p-3 bg-gray-50">
                <p className="text-xs text-muted-foreground font-bold">COMPLIANCE</p>
                <p className="text-2xl font-bold mt-1">{(biasData.complianceScore * 100).toFixed(0)}%</p>
              </div>
            </div>

            {/* Compliance Score Progress */}
            <div className="space-y-2">
              <p className="text-sm font-bold">Fairness Score</p>
              <Progress value={biasData.complianceScore * 100} className="h-3 border-2 border-black" />
            </div>

            {/* Latest Recommendations Preview */}
            {biasData.latestRecommendations && biasData.latestRecommendations.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-bold">Key Recommendations</p>
                <ul className="space-y-2">
                  {biasData.latestRecommendations.slice(0, 2).map((rec, idx) => (
                    <li key={idx} className="flex gap-2 text-sm border-l-4 border-green-500 pl-3 py-1">
                      <span className="text-green-600 font-bold mt-0.5">▸</span>
                      <span className="text-muted-foreground">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Last Evaluated Date */}
            <p className="text-xs text-muted-foreground">Last evaluated: {lastEvaluationDate}</p>

            {/* CTA Button */}
            <Link href="/dashboard/modern-bias" className="block">
              <Button className="w-full border-2 border-black font-bold shadow-brutal hover:shadow-brutal-lg">
                View Detailed Results
                <IconArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </>
        ) : (
          <div className="h-40 flex flex-col items-center justify-center text-center text-muted-foreground gap-3">
            <IconBrain className="h-8 w-8 opacity-50" />
            <div>
              <p className="font-medium">No evaluations yet</p>
              <p className="text-sm">Run a bias evaluation to get started</p>
            </div>
            <Link href="/dashboard/modern-bias">
              <Button variant="outline" size="sm" className="border-2 border-black mt-2">
                Start Evaluation
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
