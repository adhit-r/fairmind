"use client"

import * as React from "react"
import { Badge } from "@/components/ui/common/badge"

interface BiasDimension {
  dimension: string
  score: number
  threshold: number
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}

interface BiasDetectionRadarProps {
  dimensions?: BiasDimension[]
}

export function BiasDetectionRadar({ dimensions }: BiasDetectionRadarProps) {
  // Default dimensions if none provided
  const defaultDimensions: BiasDimension[] = [
    { dimension: "Gender Bias", score: 0.15, threshold: 0.2, risk_level: "LOW" },
    { dimension: "Age Bias", score: 0.25, threshold: 0.2, risk_level: "MEDIUM" },
    { dimension: "Race Bias", score: 0.35, threshold: 0.2, risk_level: "HIGH" },
    { dimension: "Income Bias", score: 0.45, threshold: 0.2, risk_level: "CRITICAL" },
    { dimension: "Education Bias", score: 0.18, threshold: 0.2, risk_level: "LOW" },
    { dimension: "Geographic Bias", score: 0.28, threshold: 0.2, risk_level: "MEDIUM" }
  ]

  const chartDimensions = dimensions || defaultDimensions

  const size = 200
  const centerX = size / 2
  const centerY = size / 2
  const radius = 80

  const getRiskColor = (level: string) => {
    switch (level) {
      case "LOW": return "#10b981"
      case "MEDIUM": return "#f59e0b"
      case "HIGH": return "#f97316"
      case "CRITICAL": return "#ef4444"
      default: return "#6b7280"
    }
  }

  const getRiskStrokeWidth = (level: string) => {
    switch (level) {
      case "CRITICAL": return 3
      case "HIGH": return 2.5
      case "MEDIUM": return 2
      case "LOW": return 1.5
      default: return 1
    }
  }

  // Calculate polygon points for radar chart
  const calculatePolygonPoints = () => {
    const numDimensions = chartDimensions.length
    const angleStep = (2 * Math.PI) / numDimensions
    
    return chartDimensions.map((dim, index) => {
      const angle = index * angleStep - Math.PI / 2 // Start from top
      const normalizedScore = Math.min(dim.score / dim.threshold, 1)
      const pointRadius = radius * normalizedScore
      const x = centerX + pointRadius * Math.cos(angle)
      const y = centerY + pointRadius * Math.sin(angle)
      return { x, y, dimension: dim.dimension, score: dim.score, risk_level: dim.risk_level }
    })
  }

  const polygonPoints = calculatePolygonPoints()
  const polygonString = polygonPoints.map(p => `${p.x},${p.y}`).join(" ")

  // Calculate axis lines
  const getAxisLines = () => {
    const numDimensions = chartDimensions.length
    const angleStep = (2 * Math.PI) / numDimensions
    
    return chartDimensions.map((dim, index) => {
      const angle = index * angleStep - Math.PI / 2
      const x1 = centerX
      const y1 = centerY
      const x2 = centerX + radius * Math.cos(angle)
      const y2 = centerY + radius * Math.sin(angle)
      return { x1, y1, x2, y2, dimension: dim.dimension, angle }
    })
  }

  const axisLines = getAxisLines()

  // Calculate concentric circles for scale
  const getConcentricCircles = () => {
    const circles = []
    for (let i = 1; i <= 4; i++) {
      const circleRadius = (radius * i) / 4
      circles.push(circleRadius)
    }
    return circles
  }

  const concentricCircles = getConcentricCircles()

  return (
    <div className="w-full h-full">
      <div className="flex flex-col items-center space-y-4">
        {/* Radar Chart */}
        <div className="relative">
          <svg width={size} height={size} className="mx-auto">
            {/* Concentric circles for scale */}
            {concentricCircles.map((circleRadius, index) => (
              <circle
                key={index}
                cx={centerX}
                cy={centerY}
                r={circleRadius}
                fill="none"
                stroke="#d1d5db"
                strokeWidth="0.5"
                strokeDasharray={index === 0 ? "none" : "2,2"}
              />
            ))}

            {/* Axis lines */}
            {axisLines.map((line, index) => (
              <g key={index}>
                <line
                  x1={line.x1}
                  y1={line.y1}
                  x2={line.x2}
                  y2={line.y2}
                  stroke="#d1d5db"
                  strokeWidth="1"
                />
                {/* Dimension labels */}
                <text
                  x={line.x2 + 15 * Math.cos(line.angle)}
                  y={line.y2 + 15 * Math.sin(line.angle)}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="text-xs fill-muted-foreground"
                  style={{ fontSize: '10px' }}
                >
                  {line.dimension}
                </text>
              </g>
            ))}

            {/* Bias polygon */}
            <polygon
              points={polygonString}
              fill="rgba(107, 114, 128, 0.1)"
              stroke="#6b7280"
              strokeWidth="2"
              fillOpacity="0.3"
            />

            {/* Data points */}
            {polygonPoints.map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r="4"
                fill={getRiskColor(point.risk_level)}
                stroke="#ffffff"
                strokeWidth="1"
              />
            ))}

            {/* Center point */}
            <circle
              cx={centerX}
              cy={centerY}
              r="3"
              fill="#6b7280"
            />
          </svg>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap justify-center gap-4 text-xs">
          {chartDimensions.map((dim, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getRiskColor(dim.risk_level) }}
              />
              <span className="text-muted-foreground">{dim.dimension}</span>
              <span className="font-mono">({dim.score.toFixed(2)})</span>
            </div>
          ))}
        </div>

        {/* Risk Level Summary */}
        <div className="flex flex-wrap justify-center gap-2">
          {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => {
            const count = chartDimensions.filter(d => d.risk_level === level).length
            if (count === 0) return null
            return (
              <Badge
                key={level}
                variant="outline"
                className="text-xs"
                style={{ 
                  borderColor: getRiskColor(level),
                  color: getRiskColor(level)
                }}
              >
                {level}: {count}
              </Badge>
            )
          })}
        </div>
      </div>
    </div>
  )
}
