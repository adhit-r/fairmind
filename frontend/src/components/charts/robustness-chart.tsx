"use client"

import * as React from "react"
import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Legend } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface RobustnessDataPoint {
  noise: string
  accuracy: number
  precision: number
  recall: number
  f1?: number
}

const mockData: RobustnessDataPoint[] = [
  { noise: '0%', accuracy: 0.92, precision: 0.91, recall: 0.89, f1: 0.90 },
  { noise: '5%', accuracy: 0.88, precision: 0.86, recall: 0.84, f1: 0.85 },
  { noise: '10%', accuracy: 0.82, precision: 0.80, recall: 0.78, f1: 0.79 },
  { noise: '15%', accuracy: 0.76, precision: 0.74, recall: 0.72, f1: 0.73 },
  { noise: '20%', accuracy: 0.70, precision: 0.68, recall: 0.65, f1: 0.66 },
  { noise: '25%', accuracy: 0.65, precision: 0.63, recall: 0.60, f1: 0.61 },
  { noise: '30%', accuracy: 0.58, precision: 0.55, recall: 0.52, f1: 0.54 },
]

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border rounded-lg p-3 shadow-sm">
        <p className="font-medium text-sm mb-2">Noise Level: {label}</p>
        <div className="space-y-1">
          {payload.map((entry, index) => (
            <div key={`tooltip-${index}`} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.stroke }}
                />
                <span className="text-xs capitalize">{entry.name}:</span>
              </div>
              <span className="text-sm font-mono">
                {(entry.value * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }
  return null
}

const CustomLegend = ({ payload }: { payload?: any[] }) => {
  if (!payload) return null
  
  return (
    <div className="flex flex-wrap justify-center gap-4 mt-2">
      {payload.map((entry, index) => (
        <div key={`legend-${index}`} className="flex items-center gap-2">
          <div 
            className="w-3 h-3 rounded-full" 
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-xs font-mono">{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

export function RobustnessChart() {
  const [data, setData] = React.useState<RobustnessDataPoint[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setLoading(true)
    
    // Simulate API call with timeout
    const timer = setTimeout(() => {
      try {
        // In a real app, you would fetch from your API
        // const response = await fetch("/api/robustness")
        // const data = await response.json()
        setData(mockData)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load robustness data')
        setLoading(false)
      }
    }, 700)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">MODEL_ROBUSTNESS</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            Loading robustness metrics...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">MODEL_ROBUSTNESS</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center text-red-500">
            Error: {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Colors for the chart lines
  const colors = {
    accuracy: 'hsl(var(--chart-1))',
    precision: 'hsl(var(--chart-2))',
    recall: 'hsl(var(--chart-3))',
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">MODEL_ROBUSTNESS</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
              data={data} 
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="hsl(var(--border))" 
                vertical={false} 
              />
              <XAxis
                dataKey="noise"
                stroke="hsl(var(--muted-foreground))"
                fontSize={10}
                fontFamily="JetBrains Mono"
                tickMargin={8}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={10} 
                fontFamily="JetBrains Mono" 
                width={40}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                domain={[0.5, 1]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                content={<CustomLegend />}
                wrapperStyle={{ 
                  paddingTop: '10px',
                }}
                formatter={(value) => (
                  <span className="text-xs">
                    {value === 'accuracy' ? 'Accuracy' : 
                     value === 'precision' ? 'Precision' : 'Recall'}
                  </span>
                )}
              />
              <Line
                name="accuracy"
                type="monotone"
                dataKey="accuracy"
                stroke={colors.accuracy}
                strokeWidth={2}
                dot={{ r: 3, stroke: colors.accuracy, strokeWidth: 1, fill: 'hsl(var(--background))' }}
                activeDot={{ r: 5, stroke: colors.accuracy, strokeWidth: 2, fill: 'hsl(var(--background))' }}
              />
              <Line
                name="precision"
                type="monotone"
                dataKey="precision"
                stroke={colors.precision}
                strokeWidth={2}
                dot={{ r: 3, stroke: colors.precision, strokeWidth: 1, fill: 'hsl(var(--background))' }}
                activeDot={{ r: 5, stroke: colors.precision, strokeWidth: 2, fill: 'hsl(var(--background))' }}
              />
              <Line
                name="recall"
                type="monotone"
                dataKey="recall"
                stroke={colors.recall}
                strokeWidth={2}
                dot={{ r: 3, stroke: colors.recall, strokeWidth: 1, fill: 'hsl(var(--background))' }}
                activeDot={{ r: 5, stroke: colors.recall, strokeWidth: 2, fill: 'hsl(var(--background))' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 text-xs text-muted-foreground text-right">
          <span className="font-mono">NOISE_IMPACT_ANALYSIS</span> • {new Date().toLocaleDateString()}
        </div>
      </CardContent>
    </Card>
  )
}
