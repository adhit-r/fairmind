'use client'

import { Card } from '@/components/ui/card'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { cn } from '@/lib/utils'
import { chartTheme, seriesColor } from '@/lib/chart-theme'

interface ChartData {
  name: string
  value: number
  [key: string]: string | number
}

interface SimpleChartProps {
  title: string
  data: ChartData[]
  type?: 'line' | 'bar'
  dataKey?: string
  className?: string
}

export function SimpleChart({
  title,
  data,
  type = 'line',
  dataKey = 'value',
  className,
}: SimpleChartProps) {
  return (
    <Card className={cn('p-4 sm:p-5', className)}>
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {type === 'line' ? (
          <LineChart data={data}>
            <CartesianGrid {...chartTheme.gridProps} />
            <XAxis dataKey="name" {...chartTheme.axisProps} />
            <YAxis {...chartTheme.axisProps} />
            <Tooltip {...chartTheme.tooltipProps} />
            <Legend {...chartTheme.legendProps} />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={seriesColor(0)}
              strokeWidth={2}
              dot={{ fill: seriesColor(0), r: 3 }}
            />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid {...chartTheme.gridProps} />
            <XAxis dataKey="name" {...chartTheme.axisProps} />
            <YAxis {...chartTheme.axisProps} />
            <Tooltip {...chartTheme.tooltipProps} />
            <Legend {...chartTheme.legendProps} />
            <Bar dataKey={dataKey} fill={seriesColor(0)} radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </Card>
  )
}
