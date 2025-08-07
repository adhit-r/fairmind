import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, User, Shield, AlertTriangle } from "lucide-react"

export default function StakeholdersPage() {
  const stakeholders = [
    {
      id: "stakeholder-001",
      name: "John Doe",
      role: "Compliance Officer",
      email: "john.doe@company.com",
      status: "Active",
      permissions: ["read", "write", "approve"]
    },
    {
      id: "stakeholder-002",
      name: "Jane Smith",
      role: "Data Scientist",
      email: "jane.smith@company.com",
      status: "Active",
      permissions: ["read", "write"]
    },
    {
      id: "stakeholder-003",
      name: "Bob Johnson",
      role: "Auditor",
      email: "bob.johnson@company.com",
      status: "Active",
      permissions: ["read"]
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Stakeholders</h1>
        <p className="text-muted-foreground">
          Manage system stakeholders and their permissions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Stakeholders</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stakeholders.map((stakeholder) => (
              <div key={stakeholder.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div>
                    <h3 className="font-medium">{stakeholder.name}</h3>
                    <p className="text-sm text-muted-foreground">{stakeholder.role} • {stakeholder.email}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <Badge variant="outline">{stakeholder.permissions.join(", ")}</Badge>
                  <Badge className="bg-green-100 text-green-800">
                    {stakeholder.status}
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