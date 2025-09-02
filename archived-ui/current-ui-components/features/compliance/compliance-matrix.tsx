"use client"

import { Badge } from "@/components/ui/common/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Progress } from "@/components/ui/common/progress"

const nistCategories = [
  {
    name: "Govern",
    description: "AI system governance and oversight",
    score: 85,
    status: "compliant",
    items: ["Policies", "Roles", "Accountability"]
  },
  {
    name: "Map",
    description: "AI system context and mapping",
    score: 78,
    status: "partial",
    items: ["Context", "Boundaries", "Stakeholders"]
  },
  {
    name: "Measure",
    description: "AI system measurement and monitoring",
    score: 92,
    status: "compliant",
    items: ["Metrics", "Monitoring", "Validation"]
  },
  {
    name: "Manage",
    description: "AI system risk management",
    score: 88,
    status: "compliant",
    items: ["Risk Assessment", "Mitigation", "Response"]
  }
]

export function ComplianceMatrix() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-500'
      case 'partial':
        return 'bg-yellow-500'
      case 'non-compliant':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'Compliant'
      case 'partial':
        return 'Partial'
      case 'non-compliant':
        return 'Non-Compliant'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {nistCategories.map((category) => (
          <Card key={category.name}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{category.name}</CardTitle>
                <div className={`h-3 w-3 rounded-full ${getStatusColor(category.status)}`} />
              </div>
              <p className="text-sm text-muted-foreground">{category.description}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold">{category.score}%</span>
                  <Badge variant={category.status === 'compliant' ? 'default' : 'secondary'}>
                    {getStatusText(category.status)}
                  </Badge>
                </div>
                <Progress value={category.score} className="h-2" />
                <div className="space-y-1">
                  {category.items.map((item) => (
                    <div key={item} className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                      <span className="text-xs text-muted-foreground">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Overall Compliance Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-green-600">85.8%</div>
            <div className="flex-1">
              <Progress value={85.8} className="h-3" />
              <p className="text-sm text-muted-foreground mt-2">
                Exceeds industry average of 72%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 