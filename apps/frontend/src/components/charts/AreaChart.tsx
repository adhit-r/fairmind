'use client'

import { Card } from '@/components/ui/card'
import {
  AreaChart as RechartsAreaChart,
  Area,
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

interface AreaChartProps {
  title: string
  data: ChartData[]
  dataKey?: string
  className?: string
}

export function AreaChart({
  title,
  data,
  dataKey = 'value',
  className,
}: AreaChartProps) {
  return (
    <Card className={cn('p-4 sm:p-5', className)}>
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsAreaChart data={data}>
          <CartesianGrid {...chartTheme.gridProps} />
          <XAxis dataKey="name" {...chartTheme.axisProps} />
          <YAxis {...chartTheme.axisProps} />
          <Tooltip {...chartTheme.tooltipProps} />
          <Legend {...chartTheme.legendProps} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={seriesColor(0)}
            strokeWidth={2}
            fill={seriesColor(0)}
            fillOpacity={0.12}
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </Card>
  )
}
