"use client"

import { Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { range: "0-10", count: 23, percentage: 2.3 },
  { range: "10-20", count: 45, percentage: 4.5 },
  { range: "20-30", count: 78, percentage: 7.8 },
  { range: "30-40", count: 134, percentage: 13.4 },
  { range: "40-50", count: 189, percentage: 18.9 },
  { range: "50-60", count: 234, percentage: 23.4 },
  { range: "60-70", count: 156, percentage: 15.6 },
  { range: "70-80", count: 89, percentage: 8.9 },
  { range: "80-90", count: 34, percentage: 3.4 },
  { range: "90-100", count: 18, percentage: 1.8 },
]

export function DistributionChart() {
  return (
    <ChartContainer
      config={{
        count: { label: "COUNT", color: "hsl(var(--chart-1))" },
      }}
      className="h-[250px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="range" stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="count" fill="hsl(var(--chart-1))" />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
