"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Eye, Play, FileText, TrendingUp, TrendingDown, Shield, Brain, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { AIGovernanceChart } from "@/components/charts/ai-governance-chart"
import { DistributionChart } from "@/components/charts/distribution-chart"
import { PerformanceMatrix } from "@/components/charts/performance-matrix"
import { NISTComplianceMatrix } from "@/components/charts/nist-compliance-matrix"
import { LLMSafetyDashboard } from "@/components/charts/llm-safety-dashboard"
import { RiskHeatmap } from "@/components/charts/risk-heatmap"
import { ModelLifecycleChart } from "@/components/charts/model-lifecycle-chart"
import { BiasDetectionRadar } from "@/components/charts/bias-detection-radar"
import { ComplianceTimeline } from "@/components/charts/compliance-timeline"
import { ModelDriftMonitor } from "@/components/charts/model-drift-monitor"
import { ExplainabilityTreemap } from "@/components/charts/explainability-treemap"

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

export function SandboxHome() {
  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
          AI_GOVERNANCE_DASHBOARD
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          COMPREHENSIVE.AI.RISK.MANAGEMENT.AND.COMPLIANCE.MONITORING.PLATFORM
        </p>
      </div>

      {/* Governance Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {governanceMetrics.map((metric) => (
          <Card key={metric.label} className="h-full">
            <CardContent className="p-4 h-full">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{metric.label}</p>
                  <p className="text-lg font-bold">{metric.value}</p>
                </div>
                <div className="flex items-center gap-2">
                  <metric.icon className="h-4 w-4" />
                  <div className="flex items-center gap-1">
                    {metric.trend.startsWith("+") ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    <span className="text-xs">{metric.trend}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Action Section */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <Link href="/simulation/new" className="w-full sm:w-auto">
            <Button className="bg-white text-black hover:bg-gray-200 w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" />
              <span className="whitespace-nowrap">NEW_SIMULATION</span>
            </Button>
          </Link>
          <Link href="/governance" className="w-full sm:w-auto">
            <Button variant="outline" className="bg-transparent w-full sm:w-auto">
              <Shield className="mr-2 h-4 w-4" />
              <span className="whitespace-nowrap">GOVERNANCE_REVIEW</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Primary Charts Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-3">
        <Card className="lg:col-span-2 min-h-[500px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">AI_GOVERNANCE_METRICS</CardTitle>
            <CardDescription className="text-xs">
              FAIRNESS.ROBUSTNESS.EXPLAINABILITY.COMPLIANCE.LLM_SAFETY
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <AIGovernanceChart />
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[500px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">BIAS_DETECTION_RADAR</CardTitle>
            <CardDescription className="text-xs">DEMOGRAPHIC.BIAS.ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <BiasDetectionRadar />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Secondary Charts Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-3">
        <Card className="min-h-[400px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">MODEL_LIFECYCLE_TRACKING</CardTitle>
            <CardDescription className="text-xs">DEVELOPMENT.TO.DEPLOYMENT.METRICS</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <ModelLifecycleChart />
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[400px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">MODEL_DRIFT_MONITORING</CardTitle>
            <CardDescription className="text-xs">REAL-TIME.DRIFT.DETECTION</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <ModelDriftMonitor />
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[400px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">COMPLIANCE_TIMELINE</CardTitle>
            <CardDescription className="text-xs">REGULATORY.ADHERENCE.TRENDS</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <ComplianceTimeline />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tertiary Charts Grid */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-2">
        <Card className="min-h-[500px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">LLM_SAFETY_ASSESSMENT</CardTitle>
            <CardDescription className="text-xs">TOXICITY.BIAS.HALLUCINATION</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <LLMSafetyDashboard />
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[500px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">RISK_DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">MODEL.RISK.SCORE.HISTOGRAM</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <DistributionChart />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feature Importance Treemap */}
      <div className="grid gap-4 md:gap-6">
        <Card className="min-h-[500px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">FEATURE_IMPORTANCE_TREEMAP</CardTitle>
            <CardDescription className="text-xs">MODEL.FEATURE.CONTRIBUTION.ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <ExplainabilityTreemap />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Matrix and NIST Compliance */}
      <div className="grid gap-4 md:gap-6 grid-cols-1">
        <Card className="min-h-[500px] flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">PERFORMANCE_MATRIX</CardTitle>
            <CardDescription className="text-xs">MODEL.PREDICTION.ACCURACY.MATRIX</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="h-full w-full">
              <PerformanceMatrix />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* NIST Compliance */}
      <div className="grid gap-4 md:gap-6">
        <NISTComplianceMatrix />
      </div>

      {/* Models and Assessments Table */}
      <Card className="overflow-x-auto">
        <CardHeader>
          <div className="flex flex-col space-y-1.5">
            <CardTitle className="text-sm">MODEL_REGISTRY_&_ASSESSMENTS</CardTitle>
            <CardDescription className="text-xs">COMPREHENSIVE.MODEL.GOVERNANCE.AND.RISK.TRACKING</CardDescription>
          </div>
          <div className="mt-2">
            <div className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input 
                placeholder="SEARCH_MODELS_AND_ASSESSMENTS..." 
                className="pl-10 font-mono text-xs h-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
            <TableHeader>
              <TableRow>
                  <TableHead className="text-xs whitespace-nowrap">MODEL_NAME</TableHead>
                <TableHead className="text-xs whitespace-nowrap">TYPE</TableHead>
                <TableHead className="text-xs whitespace-nowrap">LAST_ASSESSED</TableHead>
                <TableHead className="text-xs whitespace-nowrap">STATUS</TableHead>
                <TableHead className="text-xs whitespace-nowrap">FAIRNESS</TableHead>
                <TableHead className="text-xs whitespace-nowrap">ROBUSTNESS</TableHead>
                <TableHead className="text-xs whitespace-nowrap">EXPLAINABILITY</TableHead>
                <TableHead className="text-right text-xs whitespace-nowrap">ACTIONS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {simulations.map((simulation) => (
                <TableRow key={simulation.id}>
                  <TableCell className="font-mono text-xs">{simulation.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {simulation.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">{simulation.date}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {simulation.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs font-mono">
                    {simulation.fairness > 0 ? simulation.fairness : "--"}
                  </TableCell>
                  <TableCell className="text-xs font-mono">
                    {simulation.robustness > 0 ? simulation.robustness : "--"}
                  </TableCell>
                  <TableCell className="text-xs font-mono">
                    {simulation.explainability > 0 ? simulation.explainability : "--"}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {simulation.status === "COMPLETED" && (
                        <Link href={`/simulation/${simulation.id}/results`}>
                          <Button variant="outline" size="sm" className="text-xs bg-transparent">
                            <Eye className="mr-1 h-3 w-3" />
                            VIEW
                          </Button>
                        </Link>
                      )}
                      {simulation.status === "IN_PROGRESS" && (
                        <Link href={`/simulation/${simulation.id}/progress`}>
                          <Button variant="outline" size="sm" className="text-xs bg-transparent">
                            <Play className="mr-1 h-3 w-3" />
                            RESUME
                          </Button>
                        </Link>
                      )}
                      {simulation.status === "FAILED" && (
                        <Button variant="outline" size="sm" className="text-xs bg-transparent">
                          <FileText className="mr-1 h-3 w-3" />
                          LOGS
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
