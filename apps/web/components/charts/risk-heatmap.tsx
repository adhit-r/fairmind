"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@fairmind/ui"

const riskMatrix = [
  ["HIGH", "HIGH", "CRITICAL", "CRITICAL", "CRITICAL"],
  ["MEDIUM", "HIGH", "HIGH", "CRITICAL", "CRITICAL"],
  ["LOW", "MEDIUM", "HIGH", "HIGH", "CRITICAL"],
  ["LOW", "LOW", "MEDIUM", "HIGH", "HIGH"],
  ["LOW", "LOW", "LOW", "MEDIUM", "HIGH"],
]

const riskLabels = {
  probability: ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
  impact: ["MINIMAL", "MINOR", "MODERATE", "MAJOR", "SEVERE"],
}

export function RiskHeatmap() {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "CRITICAL":
        return "bg-white text-black"
      case "HIGH":
        return "bg-gray-300 text-black"
      case "MEDIUM":
        return "bg-gray-500 text-white"
      case "LOW":
        return "bg-gray-700 text-white"
      default:
        return "bg-gray-800 text-white"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">RISK_PROBABILITY_×_IMPACT_MATRIX</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="grid grid-cols-6 gap-1 text-xs">
            <div className="p-2 text-center font-bold">IMPACT →</div>
            {riskLabels.impact.map((label) => (
              <div key={label} className="p-2 text-center font-bold">
                {label}
              </div>
            ))}
          </div>
          {riskMatrix.map((row, i) => (
            <div key={i} className="grid grid-cols-6 gap-1 text-xs">
              <div className="p-2 text-center font-bold">
                {i === 2 ? "PROBABILITY ↓" : riskLabels.probability[4 - i]}
              </div>
              {row.map((risk, j) => (
                <div key={j} className={`p-2 text-center font-bold ${getRiskColor(risk)}`}>
                  {risk}
                </div>
              ))}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
