"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const nistFramework = [
  { function: "GOVERN", subcategories: 19, completed: 16, compliance: 84 },
  { function: "MAP", subcategories: 18, completed: 14, compliance: 78 },
  { function: "MEASURE", subcategories: 22, completed: 18, compliance: 82 },
  { function: "MANAGE", subcategories: 13, completed: 11, compliance: 85 },
]

const riskCategories = [
  { category: "FAIRNESS_&_BIAS", risk_level: "HIGH", instances: 3, mitigated: 1 },
  { category: "EXPLAINABILITY", risk_level: "MEDIUM", instances: 5, mitigated: 4 },
  { category: "ROBUSTNESS", risk_level: "LOW", instances: 2, mitigated: 2 },
  { category: "PRIVACY", risk_level: "MEDIUM", instances: 4, mitigated: 3 },
  { category: "SAFETY", risk_level: "HIGH", instances: 2, mitigated: 2 },
]

export function NISTComplianceMatrix() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">NIST_AI_RMF_COMPLIANCE</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {nistFramework.map((item) => (
              <div key={item.function} className="flex items-center justify-between p-3 border rounded">
                <div>
                  <span className="font-bold text-sm">{item.function}</span>
                  <div className="text-xs text-muted-foreground">
                    {item.completed}/{item.subcategories} SUBCATEGORIES
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold">{item.compliance}%</div>
                  <Badge variant={item.compliance >= 80 ? "default" : "outline"} className="text-xs">
                    {item.compliance >= 80 ? "COMPLIANT" : "NEEDS_WORK"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">RISK_ASSESSMENT_MATRIX</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {riskCategories.map((item) => (
              <div key={item.category} className="flex items-center justify-between p-3 border rounded">
                <div>
                  <span className="font-bold text-sm">{item.category}</span>
                  <div className="text-xs text-muted-foreground">
                    {item.mitigated}/{item.instances} MITIGATED
                  </div>
                </div>
                <div className="text-right">
                  <Badge
                    variant={
                      item.risk_level === "HIGH" ? "destructive" : item.risk_level === "MEDIUM" ? "outline" : "default"
                    }
                    className="text-xs"
                  >
                    {item.risk_level}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
