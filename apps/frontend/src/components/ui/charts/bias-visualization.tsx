"use client"

import { useState } from 'react'
import { Download, Share, Eye } from 'lucide-react'

interface BiasVisualizationProps {
  type: 'bar' | 'pie' | 'line' | 'radar'
  title: string
  data: any
  description: string
}

export function BiasVisualization({ type, title, data, description }: BiasVisualizationProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return (
          <div className="flex items-end justify-between h-full space-x-2">
            {data.labels.map((label: string, index: number) => (
              <div key={index} className="flex flex-col items-center space-y-2">
                <div
                  className="bg-blue-500 rounded-t w-full"
                  style={{
                    height: `${(data.datasets[0].data[index] * 100)}%`
                  }}
                ></div>
                <span className="text-xs font-bold text-gray-600 text-center">{label}</span>
                <span className="text-xs font-bold text-gray-900">{(data.datasets[0].data[index] * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        )

      case 'pie':
        return (
          <div className="flex items-center justify-center h-full">
            <div className="relative w-32 h-32">
              <div className="absolute inset-0 rounded-full bg-green-500" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 100%)' }}></div>
              <div className="absolute inset-0 rounded-full bg-yellow-500" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 75% 0%, 75% 100%, 50% 100%)' }}></div>
              <div className="absolute inset-0 rounded-full bg-red-500" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 60% 0%, 60% 100%, 50% 100%)' }}></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-black text-gray-900">Bias</span>
              </div>
            </div>
          </div>
        )

      case 'line':
        return (
          <div className="h-full flex items-end justify-between space-x-2">
            {data.labels.map((label: string, index: number) => (
              <div key={index} className="flex flex-col items-center space-y-2">
                <div className="relative w-full">
                  <div
                    className="absolute bottom-0 w-full bg-blue-500 rounded-t"
                    style={{
                      height: `${(data.datasets[0].data[index] * 100)}%`
                    }}
                  ></div>
                  <div
                    className="absolute bottom-0 w-full bg-green-500 rounded-t opacity-75"
                    style={{
                      height: `${(data.datasets[1].data[index] * 100)}%`
                    }}
                  ></div>
                </div>
                <span className="text-xs font-bold text-gray-600">{label}</span>
              </div>
            ))}
          </div>
        )

      case 'radar':
        return (
          <div className="flex items-center justify-center h-full">
            <div className="relative w-40 h-40">
              <div className="absolute inset-0 border-2 border-gray-300 rounded-full"></div>
              <div className="absolute inset-2 border-2 border-gray-300 rounded-full"></div>
              <div className="absolute inset-4 border-2 border-gray-300 rounded-full"></div>
              <div className="absolute inset-6 border-2 border-gray-300 rounded-full"></div>
              <div className="absolute inset-8 border-2 border-gray-300 rounded-full"></div>
              
              {/* Radar points */}
              {data.labels.map((label: string, index: number) => {
                const angle = (index * 72) * (Math.PI / 180)
                const radius = 35
                const x = 50 + radius * Math.cos(angle)
                const y = 50 + radius * Math.sin(angle)
                const value = data.datasets[0].data[index]
                const valueRadius = radius * value
                const valueX = 50 + valueRadius * Math.cos(angle)
                const valueY = 50 + valueRadius * Math.sin(angle)
                
                return (
                  <div key={index}>
                    <div
                      className="absolute w-2 h-2 bg-blue-500 rounded-full"
                      style={{
                        left: `${x}%`,
                        top: `${y}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    ></div>
                    <div
                      className="absolute w-3 h-3 bg-blue-600 rounded-full"
                      style={{
                        left: `${valueX}%`,
                        top: `${valueY}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    ></div>
                  </div>
                )
              })}
            </div>
          </div>
        )

      default:
        return <div className="text-center text-gray-500">Chart type not supported</div>
    }
  }

  return (
    <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-black text-gray-900">{title}</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
          >
            <Eye className="h-4 w-4 text-gray-700" />
          </button>
          <button className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200">
            <Download className="h-4 w-4 text-gray-700" />
          </button>
          <button className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200">
            <Share className="h-4 w-4 text-gray-700" />
          </button>
        </div>
      </div>
      
      <p className="text-sm font-bold text-gray-600 mb-4">{description}</p>
      
      <div className={`bg-gray-50 border-2 border-gray-200 rounded-lg p-4 transition-all duration-300 ${
        isExpanded ? 'h-80' : 'h-64'
      }`}>
        {renderChart()}
      </div>
      
      <div className="mt-4 flex justify-between items-center">
        <div className="flex space-x-2">
          <span className="text-xs font-bold text-gray-500">Type: {type.toUpperCase()}</span>
          <span className="text-xs font-bold text-gray-500">Data Points: {data.labels.length}</span>
        </div>
        <button className="text-xs font-bold text-blue-600 hover:text-blue-800">
          View Details
        </button>
      </div>
    </div>
  )
}
