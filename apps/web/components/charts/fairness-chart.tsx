"use client"

import { Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { group: "18-25", score: 85, baseline: 80 },
  { group: "26-35", score: 65, baseline: 80 },
  { group: "36-45", score: 82, baseline: 80 },
  { group: "46-55", score: 78, baseline: 80 },
  { group: "56+", score: 71, baseline: 80 },
]

export function FairnessChart() {
  return (
    <ChartContainer
      config={{
        score: { label: "FAIRNESS_SCORE", color: "hsl(var(--chart-1))" },
        baseline: { label: "BASELINE", color: "hsl(var(--chart-2))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="group" stroke="hsl(var(--muted-foreground))" fontSize={12} fontFamily="JetBrains Mono" />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="score" fill="hsl(var(--chart-1))" />
          <Bar dataKey="baseline" fill="hsl(var(--chart-2))" />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
