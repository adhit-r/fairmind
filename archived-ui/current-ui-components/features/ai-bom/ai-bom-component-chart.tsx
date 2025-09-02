"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface AIBOMComponentChartProps {
  bomDocuments: any[]
}

export function AIBOMComponentChart({ bomDocuments }: AIBOMComponentChartProps) {
  // Calculate component types across all BOM documents
  const componentTypes = [
    'data', 'model', 'framework', 'infrastructure', 'deployment', 'monitoring', 'security', 'compliance'
  ]

  const componentData = componentTypes.map(type => {
    const count = bomDocuments.reduce((total, doc) => {
      // Count components by type from each layer
      let layerCount = 0
      
      switch (type) {
        case 'data':
          layerCount = (doc.data_layer?.data_sources?.length || 0) +
                      (doc.data_layer?.storage_solutions?.length || 0) +
                      (doc.data_layer?.preprocessing_tools?.length || 0)
          break
        case 'model':
          layerCount = (doc.model_development_layer?.model_architectures?.length || 0) +
                      (doc.model_development_layer?.training_frameworks?.length || 0)
          break
        case 'framework':
          layerCount = (doc.model_development_layer?.frameworks?.length || 0) +
                      (doc.model_development_layer?.experiment_tracking?.length || 0)
          break
        case 'infrastructure':
          layerCount = (doc.infrastructure_layer?.cloud_platforms?.length || 0) +
                      (doc.infrastructure_layer?.containerization?.length || 0)
          break
        case 'deployment':
          layerCount = (doc.deployment_layer?.model_serving?.length || 0) +
                      (doc.deployment_layer?.api_frameworks?.length || 0)
          break
        case 'monitoring':
          layerCount = (doc.monitoring_layer?.performance_monitoring?.length || 0) +
                      (doc.monitoring_layer?.model_monitoring?.length || 0)
          break
        case 'security':
          layerCount = (doc.security_layer?.data_encryption?.length || 0) +
                      (doc.security_layer?.access_control?.length || 0)
          break
        case 'compliance':
          layerCount = (doc.compliance_layer?.regulatory_frameworks?.length || 0) +
                      (doc.compliance_layer?.compliance_tools?.length || 0)
          break
      }
      
      return total + layerCount
    }, 0)

    return {
      name: type.charAt(0).toUpperCase() + type.slice(1),
      value: count,
      color: getComponentColor(type)
    }
  })

  function getComponentColor(type: string) {
    const colors = {
      data: '#3B82F6',
      model: '#8B5CF6',
      framework: '#06B6D4',
      infrastructure: '#F59E0B',
      deployment: '#10B981',
      monitoring: '#EF4444',
      security: '#84CC16',
      compliance: '#F97316'
    }
    return colors[type as keyof typeof colors] || '#6B7280'
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{label}</p>
          <p className="text-gray-600">{payload[0].value} components</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={componentData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" fill="#8884d8">
            {componentData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
