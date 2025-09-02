"use client"

import * as React from "react"
import { Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Legend } from "recharts"

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
  // Default data if none provided
  const defaultData: FairnessDataPoint[] = [
    { name: "GENDER_MALE", score: 0.85, baseline: 0.82 },
    { name: "GENDER_FEMALE", score: 0.83, baseline: 0.82 },
    { name: "AGE_18_25", score: 0.87, baseline: 0.82 },
    { name: "AGE_26_35", score: 0.84, baseline: 0.82 },
    { name: "AGE_36_45", score: 0.81, baseline: 0.82 },
    { name: "AGE_46_55", score: 0.79, baseline: 0.82 },
    { name: "RACE_WHITE", score: 0.86, baseline: 0.82 },
    { name: "RACE_BLACK", score: 0.78, baseline: 0.82 },
    { name: "RACE_HISPANIC", score: 0.80, baseline: 0.82 },
    { name: "RACE_ASIAN", score: 0.89, baseline: 0.82 }
  ]

  const chartData = data || defaultData

  return (
    <div className="w-full h-full">
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            data={chartData} 
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
    </div>
  )
}
