"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

interface AIBOMComplianceChartProps {
  bomDocuments: any[]
}

export function AIBOMComplianceChart({ bomDocuments }: AIBOMComplianceChartProps) {
  const complianceData = [
    { 
      name: 'Compliant', 
      value: bomDocuments.filter(doc => doc.overall_compliance_status === 'compliant').length,
      color: '#10B981'
    },
    { 
      name: 'Non-Compliant', 
      value: bomDocuments.filter(doc => doc.overall_compliance_status === 'non_compliant').length,
      color: '#EF4444'
    },
    { 
      name: 'Pending', 
      value: bomDocuments.filter(doc => doc.overall_compliance_status === 'pending').length,
      color: '#F59E0B'
    },
    { 
      name: 'Review Required', 
      value: bomDocuments.filter(doc => doc.overall_compliance_status === 'review_required').length,
      color: '#F97316'
    },
  ]

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-gray-600">{payload[0].value} BOM documents</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={complianceData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {complianceData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
