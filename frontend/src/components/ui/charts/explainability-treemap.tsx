"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/common/card"

interface FeatureImportance {
  feature: string
  importance: number
  size: number
}

export function ExplainabilityTreemap() {
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [featureImportance, setFeatureImportance] = React.useState<FeatureImportance[]>([
    { feature: "CREDIT_SCORE", importance: 0.34, size: 34 },
    { feature: "INCOME", importance: 0.28, size: 28 },
    { feature: "DEBT_TO_INCOME", importance: 0.22, size: 22 },
    { feature: "EMPLOYMENT_HISTORY", importance: 0.16, size: 16 },
  ])

  React.useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setLoading(false)
    }, 500)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">FEATURE_IMPORTANCE_TREEMAP</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-muted-foreground">
            Loading feature importance data...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">FEATURE_IMPORTANCE_TREEMAP</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-red-500 p-4">Error loading feature importance data: {error}</div>
        </CardContent>
      </Card>
    )
  }

  // Sort features by importance for better visualization
  const sortedFeatures = [...featureImportance].sort((a, b) => b.importance - a.importance)

  // Color gradients for the treemap
  const colors = [
    'bg-primary/90 text-primary-foreground',
    'bg-primary/70 text-primary-foreground',
    'bg-primary/50 text-primary-foreground',
    'bg-primary/30 text-primary-foreground',
  ]

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">FEATURE_IMPORTANCE_TREEMAP</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {sortedFeatures.map((feature, index) => {
            const isLarge = index === 0
            const colorClass = colors[Math.min(index, colors.length - 1)]
            
            return (
              <div
                key={feature.feature}
                className={`
                  flex items-center justify-center p-4 rounded-lg transition-all duration-200
                  hover:shadow-md hover:scale-[1.01] ${colorClass}
                  ${isLarge ? 'md:col-span-2 h-32' : 'h-24'}
                `}
              >
                <div className="text-center">
                  <div className="font-mono text-xs font-bold uppercase tracking-wider">
                    {feature.feature.replace(/_/g, ' ')}
                  </div>
                  <div className="mt-1 text-2xl font-bold">
                    {(feature.importance * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs opacity-80 mt-1">
                    Relative importance
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        <div className="mt-3 text-xs text-muted-foreground text-right">
          <span className="font-mono">MODEL_FEATURE_IMPORTANCE</span> • {new Date().toLocaleDateString()}
        </div>
      </CardContent>
    </Card>
  )
}
