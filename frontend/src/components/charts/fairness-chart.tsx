"use client"

import * as React from "react"
import { Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Legend } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface FairnessDataPoint {
  name: string
  score: number
  baseline: number
}

const mockData: FairnessDataPoint[] = [
  { name: "AGE_GROUP_18_25", score: 0.85, baseline: 0.78 },
  { name: "AGE_GROUP_26_35", score: 0.89, baseline: 0.82 },
  { name: "AGE_GROUP_36_50", score: 0.92, baseline: 0.85 },
  { name: "AGE_GROUP_51_65", score: 0.88, baseline: 0.83 },
  { name: "AGE_GROUP_65_PLUS", score: 0.82, baseline: 0.79 },
  { name: "GENDER_MALE", score: 0.87, baseline: 0.85 },
  { name: "GENDER_FEMALE", score: 0.86, baseline: 0.84 },
  { name: "GENDER_OTHER", score: 0.84, baseline: 0.82 },
]

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) => {
  if (active && payload && payload.length) {
    const score = payload.find(item => item.dataKey === 'score')?.value
    const baseline = payload.find(item => item.dataKey === 'baseline')?.value
    
    return (
      <div className="bg-background border rounded-lg p-3 shadow-sm">
        <p className="font-medium text-sm">{label?.replace(/_/g, ' ')}</p>
        <div className="mt-2 space-y-1">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary"></div>
              <span className="text-xs">Current Score</span>
            </div>
            <span className="text-sm font-mono">{(score * 100).toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-muted-foreground/50"></div>
              <span className="text-xs">Baseline</span>
            </div>
            <span className="text-sm font-mono">{(baseline * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    )
  }
  return null
}

export function FairnessChart() {
  const [data, setData] = React.useState<FairnessDataPoint[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setLoading(true)
    
    // Simulate API call with timeout
    const timer = setTimeout(() => {
      try {
        // In a real app, you would fetch from your API
        // const response = await fetch("/api/fairness")
        // const data = await response.json()
        setData(mockData)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fairness data')
        setLoading(false)
      }
    }, 800)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">FAIRNESS_METRICS</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            Loading fairness metrics...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">FAIRNESS_METRICS</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-red-500">
            Error: {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">FAIRNESS_METRICS</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={data} 
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
              barCategoryGap={10}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={10} 
                fontFamily="JetBrains Mono"
                tickFormatter={(value) => {
                  // Shorten long labels for better display
                  const parts = value.split('_')
                  if (parts.length > 2) {
                    return parts[parts.length - 1] // Return just the last part (e.g., "MALE")
                  }
                  return value
                }}
                tickMargin={8}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={10} 
                fontFamily="JetBrains Mono" 
                domain={[0, 1]}
                tickFormatter={(value) => (value * 100).toFixed(0) + '%'}
                width={40}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                wrapperStyle={{ 
                  paddingTop: '20px',
                  fontSize: '12px',
                }}
                formatter={(value) => (
                  <span className="text-xs">
                    {value === 'score' ? 'Current Score' : 'Baseline'}
                  </span>
                )}
              />
              <Bar 
                name="score"
                dataKey="score" 
                fill="hsl(var(--primary))" 
                radius={[4, 4, 0, 0]}
              />
              <Bar 
                name="baseline"
                dataKey="baseline" 
                fill="hsl(var(--muted-foreground))"
                fillOpacity={0.5}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
