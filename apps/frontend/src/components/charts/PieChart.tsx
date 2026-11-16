'use client'

import { Card } from '@/components/ui/card'
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts'
import { cn } from '@/lib/utils'
import { chartTheme, seriesColor } from '@/lib/chart-theme'

interface PieChartData {
  name: string
  value: number
  /** Optional explicit colour (use a token such as CHART_TONES.critical). */
  color?: string
}

interface PieChartProps {
  title: string
  data: PieChartData[]
  className?: string
}

export function PieChart({ title, data, className }: PieChartProps) {
  return (
    <Card className={cn('p-4 sm:p-5', className)}>
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={100}
            dataKey="value"
            stroke="var(--card)"
            strokeWidth={2}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || seriesColor(index)}
                stroke="var(--card)"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip {...chartTheme.tooltipProps} />
          <Legend {...chartTheme.legendProps} />
        </RechartsPieChart>
      </ResponsiveContainer>
    </Card>
  )
}
