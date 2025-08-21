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
  labels: ['18-25', '26-35', '36-45', '46-55', '56-65', '65+'],
  datasets: [
    {
      label: 'Male',
      data: [25, 30, 22, 15, 8, 5],
      backgroundColor: 'rgba(136, 132, 216, 0.8)',
      borderColor: '#8884d8',
      borderWidth: 1,
    },
    {
      label: 'Female',
      data: [28, 32, 20, 12, 6, 3],
      backgroundColor: 'rgba(255, 99, 132, 0.8)',
      borderColor: '#ff6384',
      borderWidth: 1,
    },
    {
      label: 'Other',
      data: [5, 8, 6, 3, 2, 1],
      backgroundColor: 'rgba(255, 198, 88, 0.8)',
      borderColor: '#ffc658',
      borderWidth: 1,
    },
  ],
};

export function DistributionChart() {
  return (
    <div className="w-full h-full">
      <Bar options={options} data={data} />
    </div>
  );
}
