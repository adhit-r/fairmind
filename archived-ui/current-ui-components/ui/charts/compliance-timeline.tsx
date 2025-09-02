"use client"

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

interface ComplianceTimelineProps {
  data?: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      backgroundColor: string
      borderColor: string
      borderWidth: number
    }[]
  }
}

export function ComplianceTimeline({ data }: ComplianceTimelineProps) {
  const defaultData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    datasets: [
      {
        label: 'NIST Compliance',
        data: [65, 72, 78, 82, 85, 88, 90, 92, 94, 96, 98, 99],
        backgroundColor: 'rgba(17, 17, 17, 0.85)',
        borderColor: 'rgba(17, 17, 17, 1)',
        borderWidth: 1,
      },
      {
        label: 'GDPR Compliance',
        data: [70, 75, 80, 85, 88, 90, 92, 94, 96, 98, 99, 100],
        backgroundColor: 'rgba(107, 114, 128, 0.85)',
        borderColor: 'rgba(107, 114, 128, 1)',
        borderWidth: 1,
      },
      {
        label: 'ISO Compliance',
        data: [60, 68, 75, 80, 85, 88, 90, 92, 94, 96, 98, 99],
        backgroundColor: 'rgba(156, 163, 175, 0.85)',
        borderColor: 'rgba(156, 163, 175, 1)',
        borderWidth: 1,
      },
    ],
  }

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#374151',
          usePointStyle: true,
          padding: 20,
        },
      },
      title: {
        display: true,
        text: 'Regulatory Compliance Timeline',
        color: '#111827',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#e5e7eb',
        borderWidth: 1,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          color: '#6b7280',
          callback: function(value) {
            return value + '%'
          }
        },
        grid: { display: false },
      },
      x: {
        ticks: {
          color: '#6b7280',
        },
        grid: { display: false },
      },
    },
  }

  const chartData = data || defaultData

  return (
    <div className="w-full h-80">
      <Bar data={chartData} options={options} />
    </div>
  )
}
