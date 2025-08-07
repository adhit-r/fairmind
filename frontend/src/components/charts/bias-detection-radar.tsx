"use client"

import { useEffect, useRef } from 'react'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js'
import { Radar } from 'react-chartjs-2'

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
)

interface BiasDetectionRadarProps {
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

export function BiasDetectionRadar({ data }: BiasDetectionRadarProps) {
  const defaultData = {
    labels: ['Age', 'Gender', 'Race', 'Income', 'Education', 'Geography'],
    datasets: [
      {
        label: 'Current Model',
        data: [65, 78, 45, 82, 70, 58],
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
      },
      {
        label: 'Baseline',
        data: [50, 50, 50, 50, 50, 50],
        backgroundColor: 'rgba(156, 163, 175, 0.2)',
        borderColor: 'rgba(156, 163, 175, 1)',
        borderWidth: 2,
      },
    ],
  }

  const options: ChartOptions<'radar'> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        min: 0,
        ticks: {
          stepSize: 20,
          color: '#6b7280',
        },
        grid: {
          color: '#e5e7eb',
        },
        pointLabels: {
          color: '#374151',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
        },
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#374151',
          usePointStyle: true,
          padding: 20,
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
  }

  return (
    <div className="w-full h-80">
      <Radar data={data || defaultData} options={options} />
    </div>
  )
}
