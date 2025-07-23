"use client"

import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const lifecycleData = [
  { stage: "DEVELOPMENT", accuracy: 0, fairness: 0, robustness: 0, explainability: 0 },
  { stage: "TRAINING", accuracy: 65, fairness: 45, robustness: 50, explainability: 30 },
  { stage: "VALIDATION", accuracy: 78, fairness: 62, robustness: 68, explainability: 55 },
  { stage: "TESTING", accuracy: 85, fairness: 78, robustness: 82, explainability: 70 },
  { stage: "DEPLOYMENT", accuracy: 87, fairness: 80, robustness: 85, explainability: 72 },
  { stage: "MONITORING", accuracy: 84, fairness: 76, robustness: 81, explainability: 69 },
  { stage: "MAINTENANCE", accuracy: 86, fairness: 79, robustness: 84, explainability: 71 },
]

export function ModelLifecycleChart() {
  return (
    <ChartContainer
      config={{
        accuracy: { label: "ACCURACY", color: "hsl(var(--chart-1))" },
        fairness: { label: "FAIRNESS", color: "hsl(var(--chart-2))" },
        robustness: { label: "ROBUSTNESS", color: "hsl(var(--chart-3))" },
        explainability: { label: "EXPLAINABILITY", color: "hsl(var(--chart-4))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={lifecycleData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="stage"
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
            fontFamily="JetBrains Mono"
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ReferenceLine y={80} stroke="hsl(var(--chart-1))" strokeDasharray="5 5" />
          <Line type="monotone" dataKey="accuracy" stroke="hsl(var(--chart-1))" strokeWidth={2} />
          <Line type="monotone" dataKey="fairness" stroke="hsl(var(--chart-2))" strokeWidth={2} />
          <Line type="monotone" dataKey="robustness" stroke="hsl(var(--chart-3))" strokeWidth={2} />
          <Line type="monotone" dataKey="explainability" stroke="hsl(var(--chart-4))" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
