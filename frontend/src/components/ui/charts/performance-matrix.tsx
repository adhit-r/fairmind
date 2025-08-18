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

interface PerformanceMatrixProps {
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

export function PerformanceMatrix({ data }: PerformanceMatrixProps) {
  const defaultData = {
    labels: ['Approved', 'Denied', 'Pending', 'Review'],
    datasets: [
      {
        label: 'Approved',
        data: [847, 31, 19, 14],
        backgroundColor: 'rgba(17, 17, 17, 0.85)',
        borderColor: 'rgba(17, 17, 17, 1)',
        borderWidth: 1,
      },
      {
        label: 'Denied',
        data: [23, 756, 22, 19],
        backgroundColor: 'rgba(107, 114, 128, 0.85)',
        borderColor: 'rgba(107, 114, 128, 1)',
        borderWidth: 1,
      },
      {
        label: 'Pending',
        data: [12, 18, 689, 31],
        backgroundColor: 'rgba(156, 163, 175, 0.85)',
        borderColor: 'rgba(156, 163, 175, 1)',
        borderWidth: 1,
      },
      {
        label: 'Review',
        data: [8, 15, 24, 712],
        backgroundColor: 'rgba(209, 213, 219, 0.85)',
        borderColor: 'rgba(209, 213, 219, 1)',
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
        text: 'Model Prediction Accuracy Matrix',
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
        ticks: {
          color: '#6b7280',
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
