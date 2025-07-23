"use client"

import { Area, AreaChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { time: "00:00", bias_score: 78, drift_score: 92, explainability: 70 },
  { time: "04:00", bias_score: 76, drift_score: 89, explainability: 72 },
  { time: "08:00", bias_score: 79, drift_score: 91, explainability: 68 },
  { time: "12:00", bias_score: 74, drift_score: 88, explainability: 71 },
  { time: "16:00", bias_score: 77, drift_score: 90, explainability: 69 },
  { time: "20:00", bias_score: 75, drift_score: 87, explainability: 73 },
  { time: "24:00", bias_score: 78, drift_score: 92, explainability: 70 },
]

export function TimeSeriesChart() {
  return (
    <ChartContainer
      config={{
        bias_score: { label: "BIAS_SCORE", color: "hsl(var(--chart-1))" },
        drift_score: { label: "DRIFT_SCORE", color: "hsl(var(--chart-2))" },
        explainability: { label: "EXPLAINABILITY", color: "hsl(var(--chart-3))" },
      }}
      className="h-[200px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Area
            type="monotone"
            dataKey="bias_score"
            stackId="1"
            stroke="hsl(var(--chart-1))"
            fill="hsl(var(--chart-1))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="drift_score"
            stackId="2"
            stroke="hsl(var(--chart-2))"
            fill="hsl(var(--chart-2))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="explainability"
            stackId="3"
            stroke="hsl(var(--chart-3))"
            fill="hsl(var(--chart-3))"
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
