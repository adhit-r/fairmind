"use client"

import { Area, AreaChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const complianceData = [
  { date: "2025-01", gdpr: 92, ccpa: 88, nist: 85, iso: 90, sox: 94 },
  { date: "2025-02", gdpr: 94, ccpa: 90, nist: 87, iso: 92, sox: 96 },
  { date: "2025-03", gdpr: 91, ccpa: 89, nist: 89, iso: 91, sox: 93 },
  { date: "2025-04", gdpr: 95, ccpa: 92, nist: 91, iso: 94, sox: 97 },
  { date: "2025-05", gdpr: 93, ccpa: 91, nist: 88, iso: 93, sox: 95 },
  { date: "2025-06", gdpr: 96, ccpa: 94, nist: 92, iso: 95, sox: 98 },
  { date: "2025-07", gdpr: 94, ccpa: 93, nist: 90, iso: 94, sox: 96 },
]

export function ComplianceTimeline() {
  return (
    <ChartContainer
      config={{
        gdpr: { label: "GDPR", color: "hsl(var(--chart-1))" },
        ccpa: { label: "CCPA", color: "hsl(var(--chart-2))" },
        nist: { label: "NIST_AI_RMF", color: "hsl(var(--chart-3))" },
        iso: { label: "ISO_27001", color: "hsl(var(--chart-4))" },
        sox: { label: "SOX", color: "hsl(var(--chart-5))" },
      }}
      className="h-[300px]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={complianceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} fontFamily="JetBrains Mono" domain={[80, 100]} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Area
            type="monotone"
            dataKey="gdpr"
            stackId="1"
            stroke="hsl(var(--chart-1))"
            fill="hsl(var(--chart-1))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="ccpa"
            stackId="2"
            stroke="hsl(var(--chart-2))"
            fill="hsl(var(--chart-2))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="nist"
            stackId="3"
            stroke="hsl(var(--chart-3))"
            fill="hsl(var(--chart-3))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="iso"
            stackId="4"
            stroke="hsl(var(--chart-4))"
            fill="hsl(var(--chart-4))"
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="sox"
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
