"use client"

import * as React from "react"
import { Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Legend } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface FairnessDataPoint {
  name: string
  score: number
  baseline: number
}

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
              <div className="w-3 h-3 rounded-full bg-foreground"></div>
              <span className="text-xs">Current Score</span>
            </div>
            <span className="text-sm font-mono">{(score * 100).toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-muted-foreground/60"></div>
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

export function FairnessChart({ data }: { data?: FairnessDataPoint[] }) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-mono">FAIRNESS_METRICS</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No fairness data yet. Run a simulation to populate.
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
               <CartesianGrid strokeDasharray="3 3" stroke="transparent" vertical={false} />
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
                fill="hsl(var(--foreground))" 
                radius={[4, 4, 0, 0]}
              />
              <Bar 
                name="baseline"
                dataKey="baseline" 
                fill="hsl(var(--muted-foreground))"
                fillOpacity={0.6}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
