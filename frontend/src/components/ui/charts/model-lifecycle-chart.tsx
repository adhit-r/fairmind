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
  Legend
)

interface ModelLifecycleChartProps {
  data?: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
      tension: number
    }[]
  }
}

export function ModelLifecycleChart({ data }: ModelLifecycleChartProps) {
  const defaultData = {
    labels: ['Development', 'Training', 'Validation', 'Testing', 'Deployment', 'Monitoring', 'Maintenance'],
    datasets: [
      {
        label: 'Model Performance',
        data: [20, 45, 70, 85, 90, 88, 92],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Fairness Score',
        data: [15, 35, 60, 75, 82, 85, 88],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Compliance Score',
        data: [25, 50, 75, 88, 92, 90, 94],
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const options: ChartOptions<'line'> = {
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
        text: 'Model Lifecycle Tracking',
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
        },
        grid: {
          color: '#e5e7eb',
        },
      },
      x: {
        ticks: {
          color: '#6b7280',
        },
        grid: {
          color: '#e5e7eb',
        },
      },
    },
  }

  return (
    <div className="w-full h-80">
      <Line data={data || defaultData} options={options} />
    </div>
  )
}
