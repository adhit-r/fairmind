"use client"

import { Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const llmSafetyData = [
  { category: "TOXICITY", score: 92, baseline: 85 },
  { category: "BIAS", score: 78, baseline: 80 },
  { category: "HALLUCINATION", score: 85, baseline: 75 },
  { category: "PRIVACY_LEAK", score: 94, baseline: 90 },
  { category: "JAILBREAK", score: 88, baseline: 85 },
  { category: "PROMPT_INJECTION", score: 91, baseline: 88 },
]

export function LLMSafetyDashboard() {
  return (
    <ChartContainer
      config={{
        score: { label: "CURRENT_SCORE", color: "hsl(var(--chart-1))" },
        baseline: { label: "BASELINE", color: "hsl(var(--chart-2))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={llmSafetyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="category"
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
            fontFamily="JetBrains Mono"
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="score" fill="hsl(var(--chart-1))" />
          <Bar dataKey="baseline" fill="hsl(var(--chart-2))" />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
