"use client"

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface AreaChartProps {
  data?: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
      tension: number
      fill: boolean
    }[]
  }
  title?: string
  subtitle?: string
  trend?: {
    value: number
    direction: 'up' | 'down'
    period: string
  }
}

export function AreaChart({ data, title, subtitle, trend }: AreaChartProps) {
  const defaultData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    datasets: [
      {
        label: 'Total Visitors',
        data: [150, 220, 180, 320, 280, 450, 380, 520, 480, 600, 550, 700],
        borderColor: 'hsl(var(--chart-1))',
        backgroundColor: 'hsl(var(--chart-1) / 0.2)',
        tension: 0.4,
        fill: true,
      },
    ],
  }

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'hsl(var(--popover))',
        titleColor: 'hsl(var(--popover-foreground))',
        bodyColor: 'hsl(var(--popover-foreground))',
        borderColor: 'hsl(var(--border))',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'hsl(var(--border))',
        },
        ticks: {
          color: 'hsl(var(--muted-foreground))',
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: 'hsl(var(--muted-foreground))',
        },
      },
    },
  }

  return (
    <div className="space-y-4">
      {(title || subtitle || trend) && (
        <div className="space-y-2">
          {title && (
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          )}
          {subtitle && (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${
                trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
              }`}>
                {trend.direction === 'up' ? '+' : ''}{trend.value}%
              </span>
              <span className="text-sm text-muted-foreground">
                {trend.period}
              </span>
            </div>
          )}
        </div>
      )}
      <div className="h-80">
        <Line data={data || defaultData} options={options} />
      </div>
    </div>
  )
} 