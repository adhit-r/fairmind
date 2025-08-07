import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Shield, CheckCircle, AlertTriangle, XCircle } from "lucide-react"

export default function CompliancePage() {
  const complianceMetrics = [
    {
      framework: "GDPR",
      status: "Compliant",
      score: 94,
      last_audit: "2024-01-15",
      next_audit: "2024-04-15"
    },
    {
      framework: "CCPA",
      status: "Compliant", 
      score: 89,
      last_audit: "2024-01-10",
      next_audit: "2024-04-10"
    },
    {
      framework: "NIST AI",
      status: "Pending",
      score: 76,
      last_audit: "2024-01-05",
      next_audit: "2024-02-05"
    },
    {
      framework: "ISO 27001",
      status: "Non-Compliant",
      score: 45,
      last_audit: "2024-01-01",
      next_audit: "2024-01-31"
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Compliance Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor compliance across all regulatory frameworks
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Compliance</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">76%</div>
            <Progress value={76} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Average across all frameworks
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">2</div>
            <p className="text-xs text-muted-foreground">
              Frameworks
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">1</div>
            <p className="text-xs text-muted-foreground">
              Under review
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Non-Compliant</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">1</div>
            <p className="text-xs text-muted-foreground">
              Needs attention
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Compliance Frameworks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {complianceMetrics.map((framework) => (
              <div key={framework.framework} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div>
                    <h3 className="font-medium">{framework.framework}</h3>
                    <p className="text-sm text-muted-foreground">
                      Last audit: {framework.last_audit}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-2xl font-bold">{framework.score}%</div>
                    <Progress value={framework.score} className="w-24" />
                  </div>
                  <Badge className={
                    framework.status === "Compliant" ? "bg-green-100 text-green-800" :
                    framework.status === "Pending" ? "bg-yellow-100 text-yellow-800" :
                    "bg-red-100 text-red-800"
                  }>
                    {framework.status}
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