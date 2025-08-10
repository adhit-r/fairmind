"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type RiskLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
type RiskMatrix = RiskLevel[][]

const riskMatrix: RiskMatrix = [
  ["HIGH", "HIGH", "CRITICAL", "CRITICAL", "CRITICAL"],
  ["MEDIUM", "HIGH", "HIGH", "CRITICAL", "CRITICAL"],
  ["LOW", "MEDIUM", "HIGH", "HIGH", "CRITICAL"],
  ["LOW", "LOW", "MEDIUM", "HIGH", "HIGH"],
  ["LOW", "LOW", "LOW", "MEDIUM", "HIGH"],
]

const riskLabels = {
  probability: ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
  impact: ["MINIMAL", "MINOR", "MODERATE", "MAJOR", "SEVERE"],
} as const

const riskDescriptions: Record<RiskLevel, { description: string; bgColor: string; textColor: string }> = {
  CRITICAL: {
    description: "Immediate action required. High probability of severe impact.",
    bgColor: "bg-red-600 dark:bg-red-700",
    textColor: "text-white"
  },
  HIGH: {
    description: "Needs attention. High impact with significant probability.",
    bgColor: "bg-orange-500 dark:bg-orange-600",
    textColor: "text-white"
  },
  MEDIUM: {
    description: "Monitor closely. Moderate impact or probability.",
    bgColor: "bg-yellow-400 dark:bg-yellow-600",
    textColor: "text-foreground"
  },
  LOW: {
    description: "Acceptable risk. Low impact or probability.",
    bgColor: "bg-green-400 dark:bg-green-700",
    textColor: "text-foreground"
  }
}

export function RiskHeatmap({
  matrix,
  probabilityLabels,
  impactLabels,
}: {
  matrix?: RiskLevel[][],
  probabilityLabels?: readonly string[],
  impactLabels?: readonly string[],
}) {
  const [selectedRisk, setSelectedRisk] = React.useState<{
    level: RiskLevel
    probability: string
    impact: string
    x: number
    y: number
  } | null>(null)

  // Close tooltip when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.risk-cell') && !target.closest('.risk-tooltip')) {
        setSelectedRisk(null)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleRiskClick = (
    event: React.MouseEvent<HTMLDivElement>,
    risk: RiskLevel,
    rowIndex: number,
    colIndex: number
  ) => {
    event.stopPropagation()
    
    setSelectedRisk({
      level: risk,
      probability: riskLabels.probability[4 - rowIndex],
      impact: riskLabels.impact[colIndex],
      x: event.clientX,
      y: event.clientY,
    })
  }

  // Resolve data sources or show empty state
  const effectiveMatrix = matrix || null
  const prob = probabilityLabels || riskLabels.probability
  const imp = impactLabels || riskLabels.impact

  if (!effectiveMatrix) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-mono">RISK_PROBABILITY_×_IMPACT_MATRIX</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No risk data yet.
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">RISK_PROBABILITY_×_IMPACT_MATRIX</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="grid grid-cols-6 gap-1 text-xs">
            <div className="p-2 text-center font-bold text-muted-foreground">IMPACT →</div>
            {imp.map((label) => (
              <div 
                key={label} 
                className="p-2 text-center font-bold text-muted-foreground text-xs"
              >
                {label}
              </div>
            ))}
          </div>
          {effectiveMatrix.map((row, rowIndex) => (
            <div key={rowIndex} className="grid grid-cols-6 gap-1 text-xs">
              <div className="p-2 text-center font-bold text-muted-foreground text-xs">
                {rowIndex === 2 ? "PROBABILITY ↓" : prob[4 - rowIndex]}
              </div>
              {row.map((risk, colIndex) => {
                const { bgColor, textColor } = riskDescriptions[risk]
                const isSelected = selectedRisk?.x === rowIndex && selectedRisk?.y === colIndex
                
                return (
                  <div 
                    key={colIndex} 
                    className={`
                      risk-cell p-2 text-center font-bold text-xs
                      ${bgColor} ${textColor} 
                      rounded-sm transition-all duration-200 cursor-pointer
                      hover:opacity-90 hover:shadow-md
                      ${isSelected ? 'ring-2 ring-offset-2 ring-primary' : ''}
                    `}
                    onClick={(e) => handleRiskClick(e, risk, rowIndex, colIndex)}
                  >
                    {risk}
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        {/* Risk Description Tooltip */}
        {selectedRisk && (
          <div 
            className="risk-tooltip mt-4 p-4 bg-card border rounded-lg shadow-lg"
            style={{
              position: 'absolute',
              left: `${Math.min(selectedRisk.x, window.innerWidth - 300)}px`,
              top: `${selectedRisk.y + 20}px`,
              zIndex: 50,
              width: '280px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-bold">
                {selectedRisk.probability} Probability × {selectedRisk.impact} Impact
              </h4>
              <button 
                onClick={() => setSelectedRisk(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div 
                  className={`w-4 h-4 rounded-sm ${
                    riskDescriptions[selectedRisk.level].bgColor
                  }`} 
                />
                <span className="font-semibold">{selectedRisk.level} Risk</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {riskDescriptions[selectedRisk.level].description}
              </p>
              <div className="pt-2 text-xs text-muted-foreground">
                Click anywhere to close
              </div>
            </div>
          </div>
        )}

        <div className="mt-4 pt-4 border-t">
          <div className="flex flex-wrap justify-between gap-4">
            {Object.entries(riskDescriptions).map(([level, { bgColor }]) => (
              <div key={level} className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-sm ${bgColor}`} />
                <span className="text-xs">{level}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
