"use client"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const riskData = [
  {
    model: "GPT-4",
    type: "LLM",
    risk: "Low",
    bias: "Medium",
    safety: "High",
    compliance: "High",
    overall: "Low"
  },
  {
    model: "BERT-Sentiment",
    type: "NLP",
    risk: "Medium",
    bias: "Low",
    safety: "Medium",
    compliance: "High",
    overall: "Medium"
  },
  {
    model: "Recommendation-Engine",
    type: "ML",
    risk: "High",
    bias: "High",
    safety: "Medium",
    compliance: "Medium",
    overall: "High"
  },
  {
    model: "Computer-Vision",
    type: "CV",
    risk: "Medium",
    bias: "Medium",
    safety: "High",
    compliance: "High",
    overall: "Medium"
  },
  {
    model: "Decision-Tree",
    type: "ML",
    risk: "Low",
    bias: "Low",
    safety: "High",
    compliance: "High",
    overall: "Low"
  }
]

export function RiskHeatmap() {
  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getRiskScore = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low':
        return 1
      case 'medium':
        return 2
      case 'high':
        return 3
      default:
        return 0
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>AI Model Risk Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">Model</th>
                    <th className="text-left p-2 font-medium">Type</th>
                    <th className="text-left p-2 font-medium">Risk Level</th>
                    <th className="text-left p-2 font-medium">Bias Risk</th>
                    <th className="text-left p-2 font-medium">Safety Score</th>
                    <th className="text-left p-2 font-medium">Compliance</th>
                    <th className="text-left p-2 font-medium">Overall Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {riskData.map((item, index) => (
                    <tr key={index} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-medium">{item.model}</td>
                      <td className="p-2">
                        <Badge variant="outline">{item.type}</Badge>
                      </td>
                      <td className="p-2">
                        <Badge className={getRiskColor(item.risk)}>
                          {item.risk}
                        </Badge>
                      </td>
                      <td className="p-2">
                        <Badge className={getRiskColor(item.bias)}>
                          {item.bias}
                        </Badge>
                      </td>
                      <td className="p-2">
                        <Badge className={getRiskColor(item.safety)}>
                          {item.safety}
                        </Badge>
                      </td>
                      <td className="p-2">
                        <Badge className={getRiskColor(item.compliance)}>
                          {item.compliance}
                        </Badge>
                      </td>
                      <td className="p-2">
                        <Badge className={getRiskColor(item.overall)}>
                          {item.overall}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Risk Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Low Risk</span>
                  <Badge variant="outline" className="bg-green-50">2 Models</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Medium Risk</span>
                  <Badge variant="outline" className="bg-yellow-50">2 Models</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">High Risk</span>
                  <Badge variant="outline" className="bg-red-50">1 Model</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Risk Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">This Week</span>
                  <Badge className="bg-green-500">-2</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">This Month</span>
                  <Badge className="bg-yellow-500">+1</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Overall</span>
                  <Badge className="bg-green-500">-1</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Actions Required</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-red-500" />
                  <span className="text-sm">Review Recommendation Engine</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-yellow-500" />
                  <span className="text-sm">Update BERT bias detection</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-sm">All other models compliant</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 