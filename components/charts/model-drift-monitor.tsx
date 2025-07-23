"use client"

import { Line, LineChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const driftData = [
  { timestamp: "00:00", data_drift: 0.02, concept_drift: 0.01, prediction_drift: 0.03, feature_drift: 0.02 },
  { timestamp: "04:00", data_drift: 0.03, concept_drift: 0.02, prediction_drift: 0.04, feature_drift: 0.03 },
  { timestamp: "08:00", data_drift: 0.05, concept_drift: 0.03, prediction_drift: 0.06, feature_drift: 0.04 },
  { timestamp: "12:00", data_drift: 0.08, concept_drift: 0.05, prediction_drift: 0.09, feature_drift: 0.07 },
  { timestamp: "16:00", data_drift: 0.12, concept_drift: 0.08, prediction_drift: 0.13, feature_drift: 0.11 },
  { timestamp: "20:00", data_drift: 0.15, concept_drift: 0.11, prediction_drift: 0.16, feature_drift: 0.14 },
  { timestamp: "24:00", data_drift: 0.18, concept_drift: 0.13, prediction_drift: 0.19, feature_drift: 0.17 },
]

export function ModelDriftMonitor() {
  return (
    <ChartContainer
      config={{
        data_drift: { label: "DATA_DRIFT", color: "hsl(var(--chart-1))" },
        concept_drift: { label: "CONCEPT_DRIFT", color: "hsl(var(--chart-2))" },
        prediction_drift: { label: "PREDICTION_DRIFT", color: "hsl(var(--chart-3))" },
        feature_drift: { label: "FEATURE_DRIFT", color: "hsl(var(--chart-4))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={driftData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="timestamp" stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ReferenceLine y={0.1} stroke="hsl(var(--destructive))" strokeDasharray="5 5" />
          <Line type="monotone" dataKey="data_drift" stroke="hsl(var(--chart-1))" strokeWidth={2} />
          <Line type="monotone" dataKey="concept_drift" stroke="hsl(var(--chart-2))" strokeWidth={2} />
          <Line type="monotone" dataKey="prediction_drift" stroke="hsl(var(--chart-3))" strokeWidth={2} />
          <Line type="monotone" dataKey="feature_drift" stroke="hsl(var(--chart-4))" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
