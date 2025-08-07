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
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">AI_GOVERNANCE_DASHBOARD</h1>
        <p className="text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
        </p>
      </div>

      {/* Governance Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {governanceMetrics.map((metric) => (
          <Card key={metric.label}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{metric.label}</p>
                  <p className="text-lg font-bold">{metric.value}</p>
                </div>
                <div className="flex items-center gap-2">
                  <metric.icon className="h-4 w-4" />
                  <div className="flex items-center gap-1">
                    {metric.trend.startsWith("+") ? (
                      <TrendingUp className="h-3 w-3 text-green-500" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-500" />
                    )}
                    <span className="text-xs text-muted-foreground">{metric.trend}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Search and Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="SEARCH_MODELS_AND_ASSESSMENTS..." className="pl-8 w-80" />
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            NEW_SIMULATION
          </Button>
        </div>
      </div>

      {/* Model Registry Table */}
      <Card>
        <CardHeader>
          <CardTitle>MODEL_REGISTRY_&_ASSESSMENTS</CardTitle>
          <p className="text-sm text-muted-foreground font-mono">
            COMPREHENSIVE.MODEL.GOVERNANCE.AND.RISK.TRACKING
          </p>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>MODEL_NAME</TableHead>
                <TableHead>TYPE</TableHead>
                <TableHead>LAST_ASSESSED</TableHead>
                <TableHead>STATUS</TableHead>
                <TableHead>FAIRNESS</TableHead>
                <TableHead>ROBUSTNESS</TableHead>
                <TableHead>EXPLAINABILITY</TableHead>
                <TableHead>ACTION</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {simulations.map((sim) => (
                <TableRow key={sim.id}>
                  <TableCell className="font-mono">
                    <div>
                      <div className="font-medium">{sim.name}</div>
                      <div className="text-xs text-muted-foreground">{sim.model}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono">{sim.type}</Badge>
                  </TableCell>
                  <TableCell className="font-mono">{sim.date}</TableCell>
                  <TableCell>
                    <Badge className={
                      sim.status === "COMPLETED" ? "bg-green-100 text-green-800" :
                      sim.status === "IN_PROGRESS" ? "bg-yellow-100 text-yellow-800" :
                      "bg-red-100 text-red-800"
                    }>
                      {sim.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono">{sim.fairness}</TableCell>
                  <TableCell className="font-mono">{sim.robustness}</TableCell>
                  <TableCell className="font-mono">{sim.explainability}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="outline">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Risk Assessment Matrix */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>RISK_ASSESSMENT_MATRIX</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">FAIRNESS_&_BIAS</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">1/3 MITIGATED</Badge>
                  <Badge className="bg-red-100 text-red-800">HIGH</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">EXPLAINABILITY</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">4/5 MITIGATED</Badge>
                  <Badge className="bg-yellow-100 text-yellow-800">MEDIUM</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">ROBUSTNESS</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">2/2 MITIGATED</Badge>
                  <Badge className="bg-green-100 text-green-800">LOW</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">PRIVACY</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-yellow-100 text-yellow-800">3/4 MITIGATED</Badge>
                  <Badge className="bg-yellow-100 text-yellow-800">MEDIUM</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">SAFETY</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">2/2 MITIGATED</Badge>
                  <Badge className="bg-green-100 text-green-800">LOW</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>COMPLIANCE_MAP</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">GOVERNANCE</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">16/19 SUBCATEGORIES</Badge>
                  <Badge className="bg-green-100 text-green-800">84%</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">COMPLIANCE</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">14/18 SUBCATEGORIES</Badge>
                  <Badge className="bg-green-100 text-green-800">78%</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">MEASURE</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">18/22 SUBCATEGORIES</Badge>
                  <Badge className="bg-green-100 text-green-800">82%</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-mono">MANAGE</span>
                <div className="flex items-center space-x-2">
                  <Badge className="bg-green-100 text-green-800">11/13 SUBCATEGORIES</Badge>
                  <Badge className="bg-green-100 text-green-800">85%</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
