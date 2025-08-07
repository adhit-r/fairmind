import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, TrendingUp, AlertCircle, CheckCircle } from "lucide-react"

export default function RiskAssessmentPage() {
  const riskAssessments = [
    {
      id: "risk-001",
      model: "GPT-4",
      risk_type: "Bias",
      severity: "High",
      probability: "Medium",
      impact: "High",
      status: "Active",
      description: "Potential gender bias in hiring recommendations"
    },
    {
      id: "risk-002",
      model: "ResNet-50",
      risk_type: "Privacy",
      severity: "Medium",
      probability: "Low",
      impact: "Medium",
      status: "Mitigated",
      description: "Data privacy concerns in image processing"
    },
    {
      id: "risk-003",
      model: "Claude-3",
      risk_type: "Safety",
      severity: "Low",
      probability: "Low",
      impact: "Low",
      status: "Resolved",
      description: "Hallucination risk in medical advice"
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Risk Assessment</h1>
        <p className="text-muted-foreground">
          Monitor and manage AI model risks
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Risks</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{riskAssessments.length}</div>
            <p className="text-xs text-muted-foreground">
              Identified risks
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {riskAssessments.filter(r => r.severity === "High").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Critical issues
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {riskAssessments.filter(r => r.status === "Active").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Under monitoring
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {riskAssessments.filter(r => r.status === "Resolved").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Successfully addressed
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Risk Assessments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {riskAssessments.map((risk) => (
              <div key={risk.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div>
                    <h3 className="font-medium">{risk.model}</h3>
                    <p className="text-sm text-muted-foreground">{risk.description}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <Badge variant="outline">{risk.risk_type}</Badge>
                  <Badge className={
                    risk.severity === "High" ? "bg-red-100 text-red-800" :
                    risk.severity === "Medium" ? "bg-yellow-100 text-yellow-800" :
                    "bg-green-100 text-green-800"
                  }>
                    {risk.severity}
                  </Badge>
                  <Badge className={
                    risk.status === "Active" ? "bg-orange-100 text-orange-800" :
                    risk.status === "Resolved" ? "bg-green-100 text-green-800" :
                    "bg-blue-100 text-blue-800"
                  }>
                    {risk.status}
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