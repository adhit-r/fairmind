
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
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const data = [
  { time: "00:00", fairness_score: 78, robustness_score: 92, explainability: 70, compliance_rate: 89, llm_safety: 85 },
  { time: "04:00", fairness_score: 76, robustness_score: 89, explainability: 72, compliance_rate: 91, llm_safety: 87 },
  { time: "08:00", fairness_score: 79, robustness_score: 91, explainability: 68, compliance_rate: 88, llm_safety: 83 },
  { time: "12:00", fairness_score: 74, robustness_score: 88, explainability: 71, compliance_rate: 92, llm_safety: 89 },
  { time: "16:00", fairness_score: 77, robustness_score: 90, explainability: 69, compliance_rate: 87, llm_safety: 86 },
  { time: "20:00", fairness_score: 81, robustness_score: 93, explainability: 73, compliance_rate: 90, llm_safety: 88 },
];

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

const chartData = {
  labels: data.map(d => d.time),
  datasets: [
    {
      label: 'Fairness',
      data: data.map(d => d.fairness_score),
      borderColor: '#8884d8',
      backgroundColor: 'rgba(136, 132, 216, 0.3)',
      fill: true,
      tension: 0.4,
    },
    {
      label: 'Robustness',
      data: data.map(d => d.robustness_score),
      borderColor: '#82ca9d',
      backgroundColor: 'rgba(130, 202, 157, 0.3)',
      fill: true,
      tension: 0.4,
    },
    {
      label: 'Explainability',
      data: data.map(d => d.explainability),
      borderColor: '#ffc658',
      backgroundColor: 'rgba(255, 198, 88, 0.3)',
      fill: true,
      tension: 0.4,
    },
    {
      label: 'Compliance',
      data: data.map(d => d.compliance_rate),
      borderColor: '#ff7300',
      backgroundColor: 'rgba(255, 115, 0, 0.3)',
      fill: true,
      tension: 0.4,
    },
    {
      label: 'LLM Safety',
      data: data.map(d => d.llm_safety),
      borderColor: '#00C49F',
      backgroundColor: 'rgba(0, 196, 159, 0.3)',
      fill: true,
      tension: 0.4,
    },
  ],
};

export function AIGovernanceChart() {
  return (
    <div className="w-full h-full">
      <Line options={options} data={chartData} />
    </div>
  );
}
