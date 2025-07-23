"use client"

import { Area, AreaChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { time: "00:00", fairness_score: 78, robustness_score: 92, explainability: 70, compliance_rate: 89, llm_safety: 85 },
  { time: "04:00", fairness_score: 76, robustness_score: 89, explainability: 72, compliance_rate: 91, llm_safety: 87 },
  { time: "08:00", fairness_score: 79, robustness_score: 91, explainability: 68, compliance_rate: 88, llm_safety: 83 },
  { time: "12:00", fairness_score: 74, robustness_score: 88, explainability: 71, compliance_rate: 92, llm_safety: 89 },
  { time: "16:00", fairness_score: 77, robustness_score: 90, explainability: 69, compliance_rate: 87, llm_safety: 86 },
  { time: "20:00", fairness_score: 75, robustness_score: 87, explainability: 73, compliance_rate: 90, llm_safety: 88 },
  { time: "24:00", fairness_score: 78, robustness_score: 92, explainability: 70, compliance_rate: 89, llm_safety: 85 },
]

export function AIGovernanceChart() {
  return (
    <ChartContainer
      config={{
        fairness_score: { label: "FAIRNESS", color: "hsl(var(--chart-1))" },
        robustness_score: { label: "ROBUSTNESS", color: "hsl(var(--chart-2))" },
        explainability: { label: "EXPLAINABILITY", color: "hsl(var(--chart-3))" },
        compliance_rate: { label: "COMPLIANCE", color: "hsl(var(--chart-4))" },
        llm_safety: { label: "LLM_SAFETY", color: "hsl(var(--chart-5))" },
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
            dataKey="fairness_score"
            stackId="1"
            stroke="hsl(var(--chart-1))"
            fill="hsl(var(--chart-1))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="robustness_score"
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
          <Area
            type="monotone"
            dataKey="compliance_rate"
            stackId="4"
            stroke="hsl(var(--chart-4))"
            fill="hsl(var(--chart-4))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="llm_safety"
            stackId="5"
            stroke="hsl(var(--chart-5))"
            fill="hsl(var(--chart-5))"
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
