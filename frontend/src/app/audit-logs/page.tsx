import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ClipboardList, Clock, AlertTriangle, CheckCircle } from "lucide-react"

export default function AuditLogsPage() {
  const logs = [
    {
      id: "log-001",
      action: "Model Upload",
      user: "john.doe@company.com",
      timestamp: "2024-01-15 14:30:25",
      status: "Success",
      details: "GPT-4 model uploaded successfully"
    },
    {
      id: "log-002",
      action: "Compliance Check",
      user: "jane.smith@company.com", 
      timestamp: "2024-01-15 13:45:12",
      status: "Warning",
      details: "Bias detected in hiring model"
    },
    {
      id: "log-003",
      action: "Risk Assessment",
      user: "admin@company.com",
      timestamp: "2024-01-15 12:20:08",
      status: "Success",
      details: "Risk assessment completed for ResNet-50"
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Audit Logs</h1>
        <p className="text-muted-foreground">
          Track all system activities and user actions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {logs.map((log) => (
              <div key={log.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div>
                    <h3 className="font-medium">{log.action}</h3>
                    <p className="text-sm text-muted-foreground">{log.details}</p>
                    <p className="text-xs text-muted-foreground">{log.user} • {log.timestamp}</p>
                  </div>
                </div>
                <Badge className={
                  log.status === "Success" ? "bg-green-100 text-green-800" :
                  log.status === "Warning" ? "bg-yellow-100 text-yellow-800" :
                  "bg-red-100 text-red-800"
                }>
                  {log.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 