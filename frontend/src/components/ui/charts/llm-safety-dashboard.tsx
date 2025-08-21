"use client"

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: '#9CA3AF',
        font: {
          size: 12,
        },
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: '#374151',
      borderWidth: 1,
    },
  },
  scales: {
    x: {
      grid: {
        color: '#374151',
        borderColor: '#374151',
      },
      ticks: {
        color: '#9CA3AF',
        font: {
          size: 12,
        },
      },
    },
    y: {
      grid: {
        color: '#374151',
        borderColor: '#374151',
      },
      ticks: {
        color: '#9CA3AF',
        font: {
          size: 12,
        },
      },
      min: 0,
      max: 100,
    },
  },
};

const data = {
  labels: ['Toxicity', 'Bias', 'Hallucination', 'Privacy', 'Security', 'Compliance'],
  datasets: [
    {
      label: 'Current Score',
      data: [85, 78, 92, 88, 94, 91],
      backgroundColor: [
        'rgba(136, 132, 216, 0.8)',
        'rgba(130, 202, 157, 0.8)',
        'rgba(255, 198, 88, 0.8)',
        'rgba(255, 115, 0, 0.8)',
        'rgba(0, 196, 159, 0.8)',
        'rgba(255, 99, 132, 0.8)',
      ],
      borderColor: [
        '#8884d8',
        '#82ca9d',
        '#ffc658',
        '#ff7300',
        '#00C49F',
        '#ff6384',
      ],
      borderWidth: 1,
    },
    {
      label: 'Threshold',
      data: [70, 70, 70, 70, 70, 70],
      backgroundColor: 'rgba(255, 255, 255, 0.3)',
      borderColor: '#9CA3AF',
      borderWidth: 2,
      borderDash: [5, 5],
    },
  ],
};

export function LLMSafetyDashboard() {
  return (
    <div className="w-full h-full">
      <Bar options={options} data={data} />
    </div>
  );
}
