import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Plus, Search, Eye, Play, FileText, TrendingUp, TrendingDown, Shield, Brain, AlertTriangle } from "lucide-react"
import Link from "next/link"

const simulations = [
  {
    id: "1",
    name: "LOAN_MODEL_V1",
    model: "loan_v1.pkl",
    date: "2025.07.01",
    status: "COMPLETED",
    fairness: 78,
    robustness: 90,
    explainability: 70,
    type: "TRADITIONAL_ML",
  },
  {
    id: "2",
    name: "GPT4_HIRING_ASSISTANT",
    model: "gpt-4-hiring.onnx",
    date: "2025.06.20",
    status: "IN_PROGRESS",
    fairness: 0,
    robustness: 0,
    explainability: 0,
    type: "LLM",
  },
  {
    id: "3",
    name: "CREDIT_SCORING_V3",
    model: "credit_v3.h5",
    date: "2025.06.15",
    status: "FAILED",
    fairness: 45,
    robustness: 67,
    explainability: 23,
    type: "TRADITIONAL_ML",
  },
  {
    id: "4",
    name: "CLAUDE_LEGAL_ADVISOR",
    model: "claude-legal.pkl",
    date: "2025.06.10",
    status: "COMPLETED",
    fairness: 89,
    robustness: 94,
    explainability: 82,
    type: "LLM",
  },
]

const governanceMetrics = [
  { label: "NIST_COMPLIANCE", value: "82%", trend: "+3.2%", icon: Shield },
  { label: "ACTIVE_MODELS", value: "47", trend: "+12", icon: Brain },
  { label: "CRITICAL_RISKS", value: "3", trend: "-2", icon: AlertTriangle },
  { label: "LLM_SAFETY_SCORE", value: "88%", trend: "+5.1%", icon: Brain },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to your AI governance dashboard
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Simulation
          </Button>
        </div>
      </div>

      {/* Governance Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {governanceMetrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.label}
              </CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <p className="text-xs text-muted-foreground flex items-center">
                <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
                {metric.trend}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Simulations */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Simulations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search simulations..." className="max-w-sm" />
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Fairness</TableHead>
                  <TableHead>Robustness</TableHead>
                  <TableHead>Explainability</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {simulations.map((simulation) => (
                  <TableRow key={simulation.id}>
                    <TableCell className="font-medium">{simulation.name}</TableCell>
                    <TableCell>{simulation.model}</TableCell>
                    <TableCell>{simulation.date}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          simulation.status === "COMPLETED"
                            ? "default"
                            : simulation.status === "IN_PROGRESS"
                            ? "secondary"
                            : "destructive"
                        }
                      >
                        {simulation.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{simulation.fairness}%</TableCell>
                    <TableCell>{simulation.robustness}%</TableCell>
                    <TableCell>{simulation.explainability}%</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <FileText className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Bias Detection</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Test your models for bias and fairness issues
            </p>
            <Link href="/bias-detection">
              <Button className="w-full">Start Analysis</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model DNA</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Analyze model lineage and inheritance patterns
            </p>
            <Link href="/model-dna">
              <Button className="w-full">View DNA</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Check regulatory compliance status
            </p>
            <Link href="/compliance">
              <Button className="w-full">View Status</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
