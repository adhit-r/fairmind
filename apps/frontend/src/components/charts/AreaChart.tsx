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
    <Card className={cn('p-6 border-2 border-black shadow-brutal', className)}>
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsAreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#FF6B35" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#FF6B35" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#000" />
          <XAxis dataKey="name" stroke="#000" />
          <YAxis stroke="#000" />
          <Tooltip
            contentStyle={{
              border: '2px solid #000',
              borderRadius: '0',
              backgroundColor: '#fff',
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke="#000"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorValue)"
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </Card>
  )
}

