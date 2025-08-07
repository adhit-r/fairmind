"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Target, Brain, Network, BarChart3, AlertTriangle, TrendingUp, TrendingDown, Eye, Play, FileText, Globe, Users2, History, Zap, Activity } from "lucide-react"
import { BiasDetectionRadar } from "@/components/charts/bias-detection-radar"
import { DistributionChart } from "@/components/charts/distribution-chart"
import { PerformanceMatrix } from "@/components/charts/performance-matrix"

const biasDetectionMetrics = [
  { label: "SHAP ANALYSES", value: "156", trend: "+12", icon: Brain },
  { label: "LIME EXPLANATIONS", value: "89", trend: "+8", icon: Network },
  { label: "KNOWLEDGE GRAPH NODES", value: "2,847", trend: "+156", icon: Network },
  { label: "BIAS INCIDENTS", value: "12", trend: "-3", icon: AlertTriangle },
]

const shapAnalyses = [
  { model: "LOAN MODEL V1", feature: "CREDIT_SCORE", importance: 0.34, bias_contribution: 0.12, status: "ANALYZED" },
  { model: "GPT4 HIRING ASSISTANT", feature: "EDUCATION_LEVEL", importance: 0.28, bias_contribution: 0.18, status: "ANALYZED" },
  { model: "CREDIT SCORING V3", feature: "INCOME", importance: 0.22, bias_contribution: 0.25, status: "HIGH_BIAS" },
  { model: "CLAUDE LEGAL ADVISOR", feature: "LOCATION", importance: 0.16, bias_contribution: 0.08, status: "ANALYZED" },
]

const limeExplanations = [
  { model: "LOAN MODEL V1", sample: "SAMPLE_001", confidence: 0.89, bias_score: 0.15, explanation: "CREDIT_SCORE heavily influences decision" },
  { model: "GPT4 HIRING ASSISTANT", sample: "SAMPLE_002", confidence: 0.76, bias_score: 0.32, explanation: "EDUCATION_LEVEL creates unfair advantage" },
  { model: "CREDIT SCORING V3", sample: "SAMPLE_003", confidence: 0.67, bias_score: 0.28, explanation: "INCOME level significantly impacts outcome" },
  { model: "CLAUDE LEGAL ADVISOR", sample: "SAMPLE_004", confidence: 0.92, bias_score: 0.08, explanation: "LOCATION has minimal impact" },
]

const knowledgeGraphNodes = [
  { node: "CREDIT_SCORE", connections: 45, bias_propagation: 0.12, affected_groups: ["LOW_INCOME", "YOUNG_ADULTS"] },
  { node: "EDUCATION_LEVEL", connections: 32, bias_propagation: 0.18, affected_groups: ["MINORITIES", "RURAL_AREAS"] },
  { node: "INCOME", connections: 28, bias_propagation: 0.25, affected_groups: ["WOMEN", "ELDERLY"] },
  { node: "LOCATION", connections: 19, bias_propagation: 0.08, affected_groups: ["URBAN_VS_RURAL"] },
]

const biasIncidents = [
  { model: "LOAN MODEL V1", incident: "GEOGRAPHIC BIAS DETECTED", severity: "MEDIUM", time: "2 min ago", status: "INVESTIGATING" },
  { model: "GPT4 HIRING ASSISTANT", incident: "GENDER BIAS THRESHOLD EXCEEDED", severity: "HIGH", time: "5 min ago", status: "MITIGATING" },
  { model: "CREDIT SCORING V3", incident: "AGE DISCRIMINATION PATTERN", severity: "HIGH", time: "10 min ago", status: "RESOLVED" },
  { model: "CLAUDE LEGAL ADVISOR", incident: "CULTURAL BIAS DETECTED", severity: "LOW", time: "15 min ago", status: "MONITORING" },
]

const multiDimensionalBias = [
  { dimension: "GEOGRAPHIC", bias_score: 0.15, affected_countries: 8, risk_level: "MEDIUM" },
  { dimension: "DEMOGRAPHIC", bias_score: 0.28, affected_groups: 12, risk_level: "HIGH" },
  { dimension: "TEMPORAL", bias_score: 0.08, affected_periods: 3, risk_level: "LOW" },
  { dimension: "CULTURAL", bias_score: 0.22, affected_cultures: 6, risk_level: "MEDIUM" },
]

export function BiasDetectionDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">ADVANCED BIAS DETECTION</h1>
        <p className="text-sm text-muted-foreground font-mono">
          SHAP LIME KNOWLEDGE GRAPH ANALYSIS AND MULTI-DIMENSIONAL BIAS DETECTION
        </p>
      </div>

      {/* Bias Detection Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {biasDetectionMetrics.map((metric) => (
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
        <div className="flex gap-2">
          <Button className="bg-white text-black hover:bg-gray-200">
            <Brain className="mr-2 h-4 w-4" />
            RUN SHAP ANALYSIS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Network className="mr-2 h-4 w-4" />
            GENERATE LIME EXPLANATIONS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Network className="mr-2 h-4 w-4" />
            UPDATE KNOWLEDGE GRAPH
          </Button>
        </div>
      </div>

      {/* Multi-dimensional Bias Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Target className="h-4 w-4" />
            MULTI-DIMENSIONAL BIAS ANALYSIS
          </CardTitle>
          <CardDescription className="text-xs">GEOGRAPHIC DEMOGRAPHIC TEMPORAL CULTURAL DIMENSIONS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {multiDimensionalBias.map((bias, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    bias.risk_level === "HIGH" ? "bg-red-500" :
                    bias.risk_level === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{bias.dimension} BIAS</div>
                    <div className="text-xs text-muted-foreground">Score: {bias.bias_score}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">{bias.affected_countries || bias.affected_groups || bias.affected_periods || bias.affected_cultures} AFFECTED</div>
                    <div className="text-xs text-muted-foreground">{bias.dimension.toLowerCase()} dimension</div>
                  </div>
                  <Badge variant={bias.risk_level === "HIGH" ? "destructive" : "outline"}>
                    {bias.risk_level}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* SHAP Analysis Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Brain className="h-4 w-4" />
            SHAP FEATURE IMPORTANCE ANALYSIS
          </CardTitle>
          <CardDescription className="text-xs">FEATURE CONTRIBUTION TO MODEL DECISIONS AND BIAS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>MODEL</TableHead>
                  <TableHead>FEATURE</TableHead>
                  <TableHead>IMPORTANCE</TableHead>
                  <TableHead>BIAS CONTRIBUTION</TableHead>
                  <TableHead>STATUS</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shapAnalyses.map((analysis, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{analysis.model}</div>
                    </TableCell>
                    <TableCell className="font-mono">{analysis.feature}</TableCell>
                    <TableCell className="font-mono">{analysis.importance}</TableCell>
                    <TableCell className="font-mono">{analysis.bias_contribution}</TableCell>
                    <TableCell>
                      <Badge className={
                        analysis.status === "HIGH_BIAS" ? "bg-red-100 text-red-800" :
                        analysis.status === "ANALYZED" ? "bg-green-100 text-green-800" :
                        "bg-yellow-100 text-yellow-800"
                      }>
                        {analysis.status}
                      </Badge>
                    </TableCell>
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
          </div>
        </CardContent>
      </Card>

      {/* LIME Explanations Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Network className="h-4 w-4" />
            LIME LOCAL EXPLANATIONS
          </CardTitle>
          <CardDescription className="text-xs">LOCAL INTERPRETABLE MODEL EXPLANATIONS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {limeExplanations.map((explanation, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    explanation.bias_score > 0.25 ? "bg-red-500" :
                    explanation.bias_score > 0.15 ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{explanation.model} - {explanation.sample}</div>
                    <div className="text-xs text-muted-foreground">{explanation.explanation}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Confidence: {explanation.confidence}</div>
                    <div className="text-xs text-muted-foreground">Bias: {explanation.bias_score}</div>
                  </div>
                  <Badge variant={explanation.bias_score > 0.25 ? "destructive" : "outline"}>
                    {explanation.bias_score > 0.25 ? "HIGH" : explanation.bias_score > 0.15 ? "MEDIUM" : "LOW"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Knowledge Graph Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Network className="h-4 w-4" />
            KNOWLEDGE GRAPH BIAS PROPAGATION
          </CardTitle>
          <CardDescription className="text-xs">CAUSAL RELATIONSHIPS AND BIAS SPREAD PATTERNS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {knowledgeGraphNodes.map((node, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    node.bias_propagation > 0.2 ? "bg-red-500" :
                    node.bias_propagation > 0.1 ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{node.node}</div>
                    <div className="text-xs text-muted-foreground">{node.connections} connections</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Propagation: {node.bias_propagation}</div>
                    <div className="text-xs text-muted-foreground">{node.affected_groups.join(", ")}</div>
                  </div>
                  <Badge variant={node.bias_propagation > 0.2 ? "destructive" : "outline"}>
                    {node.bias_propagation > 0.2 ? "HIGH" : node.bias_propagation > 0.1 ? "MEDIUM" : "LOW"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Bias Incidents Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            ACTIVE BIAS INCIDENTS
          </CardTitle>
          <CardDescription className="text-xs">REAL-TIME BIAS DETECTION AND MITIGATION</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {biasIncidents.map((incident, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`h-4 w-4 ${
                    incident.severity === "HIGH" ? "text-red-500" :
                    incident.severity === "MEDIUM" ? "text-yellow-500" : "text-blue-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{incident.incident}</div>
                    <div className="text-xs text-muted-foreground">{incident.model}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={incident.severity === "HIGH" ? "destructive" : "outline"}>
                    {incident.severity}
                  </Badge>
                  <Badge variant="outline">{incident.status}</Badge>
                  <span className="text-xs text-muted-foreground">{incident.time}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">BIAS DETECTION RADAR</CardTitle>
            <CardDescription className="text-xs">MULTI-DIMENSIONAL BIAS ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent>
            <BiasDetectionRadar />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">BIAS DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">BIAS SCORE DISTRIBUTION PATTERNS</CardDescription>
          </CardHeader>
          <CardContent>
            <DistributionChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">PERFORMANCE MATRIX</CardTitle>
            <CardDescription className="text-xs">BIAS VS PERFORMANCE TRADE-OFF</CardDescription>
          </CardHeader>
          <CardContent>
            <PerformanceMatrix />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
