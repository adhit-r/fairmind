'use client'

import { Card } from '@/components/ui/card'
import {
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { cn } from '@/lib/utils'
import { chartTheme, seriesColor } from '@/lib/chart-theme'

interface RadarChartData {
  subject: string
  value: number
  fullMark?: number
}

interface RadarChartProps {
  title: string
  data: RadarChartData[]
  className?: string
}

export function RadarChart({ title, data, className }: RadarChartProps) {
  return (
    <Card className={cn('p-4 sm:p-5', className)}>
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsRadarChart data={data}>
          <PolarGrid stroke={chartTheme.grid} />
          <PolarAngleAxis dataKey="subject" tick={chartTheme.axisProps.tick} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={chartTheme.axisProps.tick} stroke={chartTheme.axis} />
          <Radar
            name="Score"
            dataKey="value"
            stroke={seriesColor(0)}
            fill={seriesColor(0)}
            fillOpacity={0.2}
            strokeWidth={2}
          />
          <Legend {...chartTheme.legendProps} />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </Card>
  )
}
