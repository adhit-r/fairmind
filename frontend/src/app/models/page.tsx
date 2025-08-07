import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Database, Eye, Edit, Trash2, Plus } from "lucide-react"

export default function ModelsPage() {
  const models = [
    {
      id: "model-001",
      name: "GPT-4",
      version: "4.0",
      type: "LLM",
      status: "Active",
      accuracy: 94,
      fairness: 87,
      compliance: "Compliant",
      risk_level: "Medium",
      last_assessed: "2024-01-15"
    },
    {
      id: "model-002", 
      name: "Claude-3",
      version: "3.0",
      type: "LLM",
      status: "Active",
      accuracy: 92,
      fairness: 91,
      compliance: "Compliant",
      risk_level: "Low",
      last_assessed: "2024-01-12"
    },
    {
      id: "model-003",
      name: "ResNet-50",
      version: "1.0",
      type: "Computer Vision",
      status: "Active",
      accuracy: 89,
      fairness: 85,
      compliance: "Pending",
      risk_level: "High",
      last_assessed: "2024-01-10"
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Model Registry</h1>
          <p className="text-muted-foreground">
            Manage and track all AI models in your organization
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Model
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Models</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.length}</div>
            <p className="text-xs text-muted-foreground">
              Registered models
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Database className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {models.filter(m => m.status === "Active").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently deployed
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant</CardTitle>
            <Database className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {models.filter(m => m.compliance === "Compliant").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Passed compliance
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <Database className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {models.filter(m => m.risk_level === "High").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Need attention
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Registered Models</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Accuracy</TableHead>
                <TableHead>Fairness</TableHead>
                <TableHead>Compliance</TableHead>
                <TableHead>Risk Level</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((model) => (
                <TableRow key={model.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{model.name}</div>
                      <div className="text-sm text-muted-foreground">v{model.version}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{model.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={model.status === "Active" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                      {model.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{model.accuracy}%</TableCell>
                  <TableCell>{model.fairness}%</TableCell>
                  <TableCell>
                    <Badge className={model.compliance === "Compliant" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                      {model.compliance}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={model.risk_level === "High" ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}>
                      {model.risk_level}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="outline">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
} 