"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface AIBOMRiskChartProps {
  bomDocuments: any[]
}

export function AIBOMRiskChart({ bomDocuments }: AIBOMRiskChartProps) {
  const riskData = [
    { name: 'Low', value: bomDocuments.filter(doc => doc.overall_risk_level === 'low').length, color: '#10B981' },
    { name: 'Medium', value: bomDocuments.filter(doc => doc.overall_risk_level === 'medium').length, color: '#F59E0B' },
    { name: 'High', value: bomDocuments.filter(doc => doc.overall_risk_level === 'high').length, color: '#F97316' },
    { name: 'Critical', value: bomDocuments.filter(doc => doc.overall_risk_level === 'critical').length, color: '#EF4444' },
  ]

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{label}</p>
          <p className="text-gray-600">{payload[0].value} BOM documents</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={riskData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" fill="#8884d8">
            {riskData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
