"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const featureImportance = [
  { feature: "CREDIT_SCORE", importance: 0.34, size: 34 },
  { feature: "INCOME", importance: 0.28, size: 28 },
  { feature: "DEBT_TO_INCOME", importance: 0.22, size: 22 },
  { feature: "EMPLOYMENT_HISTORY", importance: 0.16, size: 16 },
]

export function ExplainabilityTreemap() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">FEATURE_IMPORTANCE_TREEMAP</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 h-[200px]">
          {featureImportance.map((feature, index) => (
            <div
              key={feature.feature}
              className={`flex items-center justify-center p-4 border rounded text-center ${
                index === 0
                  ? "col-span-2 bg-white text-black"
                  : index === 1
                    ? "bg-gray-300 text-black"
                    : index === 2
                      ? "bg-gray-500 text-white"
                      : "bg-gray-700 text-white"
              }`}
              style={{ height: index === 0 ? "60%" : "40%" }}
            >
              <div>
                <div className="font-bold text-xs">{feature.feature}</div>
                <div className="text-lg font-bold">{feature.importance}</div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
