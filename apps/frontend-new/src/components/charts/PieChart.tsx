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

interface PieChartData {
  name: string
  value: number
  color?: string
}

interface PieChartProps {
  title: string
  data: PieChartData[]
  className?: string
}

const COLORS = ['#FF6B35', '#000000', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6']

export function PieChart({ title, data, className }: PieChartProps) {
  return (
    <Card className={cn('p-6 border-2 border-black shadow-brutal', className)}>
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            stroke="#000"
            strokeWidth={2}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || COLORS[index % COLORS.length]}
                stroke="#000"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              border: '2px solid #000',
              borderRadius: '0',
              backgroundColor: '#fff',
            }}
          />
          <Legend />
        </RechartsPieChart>
      </ResponsiveContainer>
    </Card>
  )
}

