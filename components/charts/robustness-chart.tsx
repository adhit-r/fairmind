"use client"

import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { noise: 0.0, accuracy: 94.2, precision: 92.1, recall: 91.8 },
  { noise: 0.1, accuracy: 92.8, precision: 90.5, recall: 89.2 },
  { noise: 0.2, accuracy: 89.1, precision: 87.3, recall: 85.9 },
  { noise: 0.3, accuracy: 84.7, precision: 82.1, recall: 80.4 },
  { noise: 0.4, accuracy: 78.3, precision: 75.8, recall: 73.2 },
  { noise: 0.5, accuracy: 69.5, precision: 67.2, recall: 64.8 },
]

export function RobustnessChart() {
  return (
    <ChartContainer
      config={{
        accuracy: { label: "ACCURACY", color: "hsl(var(--chart-1))" },
        precision: { label: "PRECISION", color: "hsl(var(--chart-2))" },
        recall: { label: "RECALL", color: "hsl(var(--chart-3))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="noise" stroke="hsl(var(--muted-foreground))" fontSize={12} fontFamily="JetBrains Mono" />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line type="monotone" dataKey="accuracy" stroke="hsl(var(--chart-1))" strokeWidth={2} />
          <Line type="monotone" dataKey="precision" stroke="hsl(var(--chart-2))" strokeWidth={2} />
          <Line type="monotone" dataKey="recall" stroke="hsl(var(--chart-3))" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
