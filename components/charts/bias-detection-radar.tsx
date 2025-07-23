"use client"

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const biasData = [
  { category: "AGE", current: 78, baseline: 85, threshold: 80 },
  { category: "GENDER", current: 82, baseline: 85, threshold: 80 },
  { category: "RACE", current: 75, baseline: 85, threshold: 80 },
  { category: "INCOME", current: 88, baseline: 85, threshold: 80 },
  { category: "EDUCATION", current: 91, baseline: 85, threshold: 80 },
  { category: "GEOGRAPHY", current: 79, baseline: 85, threshold: 80 },
]

export function BiasDetectionRadar() {
  return (
    <ChartContainer
      config={{
        current: { label: "CURRENT_SCORE", color: "hsl(var(--chart-1))" },
        baseline: { label: "BASELINE", color: "hsl(var(--chart-2))" },
        threshold: { label: "THRESHOLD", color: "hsl(var(--chart-3))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={biasData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="category"
            tick={{ fontSize: 10, fontFamily: "JetBrains Mono", fill: "hsl(var(--foreground))" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 8, fontFamily: "JetBrains Mono", fill: "hsl(var(--muted-foreground))" }}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Radar
            name="CURRENT_SCORE"
            dataKey="current"
            stroke="hsl(var(--chart-1))"
            fill="hsl(var(--chart-1))"
            fillOpacity={0.3}
            strokeWidth={2}
          />
          <Radar
            name="BASELINE"
            dataKey="baseline"
            stroke="hsl(var(--chart-2))"
            fill="hsl(var(--chart-2))"
            fillOpacity={0.1}
            strokeWidth={1}
            strokeDasharray="5 5"
          />
          <Radar
            name="THRESHOLD"
            dataKey="threshold"
            stroke="hsl(var(--chart-3))"
            fill="none"
            strokeWidth={1}
            strokeDasharray="2 2"
          />
        </RadarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
