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
  className 
}: SimpleChartProps) {
  return (
    <Card className={cn('p-6 border-2 border-black shadow-brutal', className)}>
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {type === 'line' ? (
          <LineChart data={data}>
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
            <Line 
              type="monotone" 
              dataKey={dataKey} 
              stroke="#FF6B35" 
              strokeWidth={3}
              dot={{ fill: '#000', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        ) : (
          <BarChart data={data}>
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
            <Bar 
              dataKey={dataKey} 
              fill="#FF6B35"
              stroke="#000"
              strokeWidth={2}
            />
          </BarChart>
        )}
      </ResponsiveContainer>
    </Card>
  )
}

