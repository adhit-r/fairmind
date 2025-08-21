"use client"

import * as React from "react"
import { Badge } from "@/components/ui/common/badge"

interface NISTFrameworkItem {
  function: string
  subcategories: number
  completed: number
  compliance: number
}

interface RiskCategoryItem {
  category: string
  risk_level: "LOW" | "MEDIUM" | "HIGH"
  instances: number
  mitigated: number
}

const nistFramework: NISTFrameworkItem[] = [
  { function: "GOVERN", subcategories: 8, completed: 7, compliance: 88 },
  { function: "MAP", subcategories: 6, completed: 5, compliance: 83 },
  { function: "MEASURE", subcategories: 10, completed: 8, compliance: 80 },
  { function: "MANAGE", subcategories: 12, completed: 9, compliance: 75 }
]

const riskCategories: RiskCategoryItem[] = [
  { category: "FAIRNESS_&_BIAS", risk_level: "HIGH", instances: 3, mitigated: 1 },
  { category: "EXPLAINABILITY", risk_level: "MEDIUM", instances: 5, mitigated: 4 },
  { category: "ROBUSTNESS", risk_level: "LOW", instances: 2, mitigated: 2 },
  { category: "PRIVACY", risk_level: "MEDIUM", instances: 4, mitigated: 3 },
  { category: "SAFETY", risk_level: "HIGH", instances: 2, mitigated: 2 },
]

export function NISTComplianceMatrix() {
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setLoading(false)
    }, 500)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="w-full h-full">
        <div className="h-32 flex items-center justify-center text-muted-foreground">
          Loading compliance data...
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="text-red-500 p-4">Error loading compliance data: {error}</div>
  }

  return (
    <div className="w-full h-full">
      <div className="space-y-3">
        {nistFramework.map((item) => {
          const progress = (item.completed / item.subcategories) * 100
          return (
            <div 
              key={item.function} 
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 border rounded hover:bg-accent/50 transition-colors"
            >
              <div>
                <span className="font-bold text-sm">{item.function}</span>
                <div className="text-xs text-muted-foreground">
                  {item.completed}/{item.subcategories} SUBCATEGORIES
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <div className="text-lg font-bold">{item.compliance}%</div>
                <Badge 
                  variant={item.compliance >= 80 ? "default" : "outline"} 
                  className="text-xs"
                >
                  {item.compliance >= 80 ? "COMPLIANT" : "NEEDS_WORK"}
                </Badge>
              </div>
            </div>
          )
        })}
      </div>
      
      <div className="mt-6 space-y-3">
        {riskCategories.map((item) => (
          <div 
            key={item.category} 
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 border rounded hover:bg-accent/50 transition-colors"
          >
            <div>
              <span className="font-bold text-sm">
                {item.category.replace(/_/g, ' ').replace(/&/g, ' & ')}
              </span>
              <div className="text-xs text-muted-foreground">
                {item.mitigated}/{item.instances} MITIGATED
              </div>
            </div>
            <div>
              <Badge
                variant={
                  item.risk_level === "HIGH" 
                    ? "destructive" 
                    : item.risk_level === "MEDIUM" 
                      ? "outline" 
                      : "default"
                }
                className="text-xs"
              >
                {item.risk_level}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
