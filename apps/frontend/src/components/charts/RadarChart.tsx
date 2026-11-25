'use client'

import { Card } from '@/components/ui/card'
import { describeChart } from '@/components/charts/describe'
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
    <Card className={cn('p-6 fm-card', className)}>
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      <div role="img" aria-label={describeChart(title, data.map((d) => [d.subject, d.value]))}>
        <ResponsiveContainer width="100%" height={300}>
          <RechartsRadarChart data={data}>
            <PolarGrid stroke="#000" />
            <PolarAngleAxis dataKey="subject" stroke="#000" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#000" />
            <Radar
              name="Score"
              dataKey="value"
              stroke="#000"
              fill="#FF6B35"
              fillOpacity={0.6}
              strokeWidth={2}
            />
            <Legend />
          </RechartsRadarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

