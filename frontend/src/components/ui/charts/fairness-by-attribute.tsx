"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface FairnessByAttributeProps {
  byAttribute?: Array<{
    attribute: string
    demographic_parity_difference: number
    equal_opportunity_difference?: number
    disparate_impact_ratio?: number
  }>
}

export function FairnessByAttribute({ byAttribute }: FairnessByAttributeProps) {
  if (!byAttribute || byAttribute.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-mono">FAIRNESS_BY_ATTRIBUTE</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No fairness metrics by attribute available.
          </div>
        </CardContent>
      </Card>
    )
  }

  const metrics = ['demographic_parity_difference', 'equal_opportunity_difference', 'disparate_impact_ratio'] as const

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">FAIRNESS_BY_ATTRIBUTE</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {byAttribute.map((attr) => (
            <div key={attr.attribute} className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">
                Attribute: {attr.attribute}
              </div>
              <div className="grid grid-cols-1 gap-2">
                {metrics.map((metric) => {
                  const value = attr[metric]
                  if (value === undefined) return null
                  
                  // Normalize values for display
                  let displayValue = value
                  let percentage = 0
                  let isGood = true
                  
                  if (metric === 'demographic_parity_difference' || metric === 'equal_opportunity_difference') {
                    displayValue = Math.abs(value)
                    percentage = Math.min(100, Math.round(displayValue * 100))
                    isGood = displayValue < 0.1 // Good if difference < 10%
                  } else if (metric === 'disparate_impact_ratio') {
                    displayValue = value
                    percentage = Math.round(Math.abs(1 - value) * 100)
                    isGood = Math.abs(1 - value) < 0.2 // Good if ratio close to 1
                  }
                  
                  return (
                    <div key={metric} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">
                          {metric.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        <span className="font-mono">
                          {value.toFixed(4)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
                            isGood ? 'bg-gray-800' : 'bg-red-600'
                          }`}
                          style={{ width: `${Math.min(100, percentage)}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Fairness Assessment</span>
            <span>
              {byAttribute.every(attr => Math.abs(attr.demographic_parity_difference) < 0.1) 
                ? "✓ FAIR" 
                : "⚠ BIAS DETECTED"
              }
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
