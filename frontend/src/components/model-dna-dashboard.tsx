"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dna, GitBranch, Network, TrendingUp, TrendingDown, AlertTriangle, Activity, BarChart3, Target, Users2, History, Zap } from "lucide-react"
import { DistributionChart } from "@/components/charts/distribution-chart"
import { PerformanceMatrix } from "@/components/charts/performance-matrix"

const dnaMetrics = [
  { label: "TOTAL MODELS", value: "47", trend: "+5", icon: Dna },
  { label: "DNA SIGNATURES", value: "47", trend: "+5", icon: Dna },
  { label: "PARENT RELATIONSHIPS", value: "89", trend: "+12", icon: Network },
  { label: "INHERITANCE PATTERNS", value: "156", trend: "+18", icon: GitBranch },
]

const modelDnaSignatures = [
  { model: "LOAN MODEL V1", dna_signature: "A1B2C3D4", parent_models: ["CREDIT_V2", "LOAN_V0"], inheritance_type: "HYBRID", algorithm_family: "GRADIENT_BOOSTING", bias_inheritance: 0.15 },
  { model: "GPT4 HIRING ASSISTANT", dna_signature: "E5F6G7H8", parent_models: ["GPT4_BASE", "HIRING_V1"], inheritance_type: "FINE_TUNED", algorithm_family: "TRANSFORMER", bias_inheritance: 0.32 },
  { model: "CREDIT SCORING V3", dna_signature: "I9J0K1L2", parent_models: ["CREDIT_V2", "SCORING_V2"], inheritance_type: "ENSEMBLE", algorithm_family: "RANDOM_FOREST", bias_inheritance: 0.28 },
  { model: "CLAUDE LEGAL ADVISOR", dna_signature: "M3N4O5P6", parent_models: ["CLAUDE_BASE", "LEGAL_V1"], inheritance_type: "FINE_TUNED", algorithm_family: "TRANSFORMER", bias_inheritance: 0.08 },
  { model: "FRAUD DETECTION V2", dna_signature: "Q7R8S9T0", parent_models: ["FRAUD_V1", "DETECTION_V1"], inheritance_type: "HYBRID", algorithm_family: "NEURAL_NETWORK", bias_inheritance: 0.22 },
]

const inheritancePatterns = [
  { pattern: "BIAS AMPLIFICATION", frequency: 0.35, risk_level: "HIGH", affected_models: 12, description: "Bias increases through inheritance" },
  { pattern: "BIAS MITIGATION", frequency: 0.28, risk_level: "LOW", affected_models: 8, description: "Bias decreases through inheritance" },
  { pattern: "BIAS TRANSFER", frequency: 0.22, risk_level: "MEDIUM", affected_models: 6, description: "Bias transfers unchanged" },
  { pattern: "BIAS TRANSFORMATION", frequency: 0.15, risk_level: "MEDIUM", affected_models: 4, description: "Bias changes form through inheritance" },
]

const lineageEvents = [
  { event: "MODEL FORK", model: "LOAN MODEL V1", timestamp: "2 min ago", impact: "HIGH", description: "Forked from CREDIT_V2 with bias amplification" },
  { event: "BIAS INHERITANCE", model: "GPT4 HIRING ASSISTANT", timestamp: "5 min ago", impact: "MEDIUM", description: "Inherited gender bias from GPT4_BASE" },
  { event: "ENSEMBLE CREATION", model: "CREDIT SCORING V3", timestamp: "8 min ago", impact: "LOW", description: "Combined multiple models with bias averaging" },
  { event: "FINE_TUNING", model: "CLAUDE LEGAL ADVISOR", timestamp: "12 min ago", impact: "MEDIUM", description: "Fine-tuned with bias mitigation techniques" },
]

const geneticAlgorithms = [
  { algorithm: "GRADIENT_BOOSTING", models: 15, avg_bias: 0.18, inheritance_rate: 0.75, risk_level: "MEDIUM" },
  { algorithm: "TRANSFORMER", models: 12, avg_bias: 0.25, inheritance_rate: 0.82, risk_level: "HIGH" },
  { algorithm: "RANDOM_FOREST", models: 8, avg_bias: 0.12, inheritance_rate: 0.45, risk_level: "LOW" },
  { algorithm: "NEURAL_NETWORK", models: 6, avg_bias: 0.22, inheritance_rate: 0.68, risk_level: "MEDIUM" },
  { algorithm: "SUPPORT_VECTOR", models: 4, avg_bias: 0.15, inheritance_rate: 0.52, risk_level: "LOW" },
]

export function ModelDnaDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">MODEL DNA SIGNATURES</h1>
        <p className="text-sm text-muted-foreground font-mono">
          GENETIC LINEAGE INHERITANCE TRACKING AND BIAS PROPAGATION ANALYSIS
        </p>
      </div>

      {/* DNA Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {dnaMetrics.map((metric) => (
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
            <Dna className="mr-2 h-4 w-4" />
            GENERATE DNA SIGNATURE
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Network className="mr-2 h-4 w-4" />
            TRACE LINEAGE
          </Button>
          <Button variant="outline" className="bg-transparent">
            <GitBranch className="mr-2 h-4 w-4" />
            ANALYZE INHERITANCE
          </Button>
        </div>
      </div>

      {/* Model DNA Signatures Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Dna className="h-4 w-4" />
            MODEL DNA SIGNATURES
          </CardTitle>
          <CardDescription className="text-xs">GENETIC LINEAGE AND INHERITANCE TRACKING</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>MODEL</TableHead>
                  <TableHead>DNA SIGNATURE</TableHead>
                  <TableHead>PARENT MODELS</TableHead>
                  <TableHead>INHERITANCE TYPE</TableHead>
                  <TableHead>ALGORITHM FAMILY</TableHead>
                  <TableHead>BIAS INHERITANCE</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {modelDnaSignatures.map((dna, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{dna.model}</div>
                    </TableCell>
                    <TableCell className="font-mono">
                      <div className="flex items-center gap-1">
                        <Dna className="h-3 w-3" />
                        {dna.dna_signature}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {dna.parent_models.map((parent, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {parent}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono">{dna.inheritance_type}</TableCell>
                    <TableCell className="font-mono">{dna.algorithm_family}</TableCell>
                    <TableCell className="font-mono">{dna.bias_inheritance}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button size="sm" variant="outline">
                          <Target className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <BarChart3 className="h-4 w-4" />
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

      {/* Inheritance Patterns */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            INHERITANCE PATTERNS
          </CardTitle>
          <CardDescription className="text-xs">BIAS PROPAGATION THROUGH MODEL LINEAGE</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {inheritancePatterns.map((pattern, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    pattern.risk_level === "HIGH" ? "bg-red-500" :
                    pattern.risk_level === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{pattern.pattern}</div>
                    <div className="text-xs text-muted-foreground">{pattern.description}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Frequency: {pattern.frequency}</div>
                    <div className="text-xs text-muted-foreground">{pattern.affected_models} models</div>
                  </div>
                  <Badge variant={pattern.risk_level === "HIGH" ? "destructive" : "outline"}>
                    {pattern.risk_level}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Lineage Events */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <History className="h-4 w-4" />
            LINEAGE EVENTS
          </CardTitle>
          <CardDescription className="text-xs">RECENT MODEL EVOLUTION AND INHERITANCE EVENTS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {lineageEvents.map((event, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    event.impact === "HIGH" ? "bg-red-500" :
                    event.impact === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{event.event} - {event.model}</div>
                    <div className="text-xs text-muted-foreground">{event.description}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={event.impact === "HIGH" ? "destructive" : "outline"}>
                    {event.impact}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{event.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Genetic Algorithms Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Network className="h-4 w-4" />
            GENETIC ALGORITHMS ANALYSIS
          </CardTitle>
          <CardDescription className="text-xs">ALGORITHM FAMILY BIAS INHERITANCE PATTERNS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {geneticAlgorithms.map((algorithm, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    algorithm.risk_level === "HIGH" ? "bg-red-500" :
                    algorithm.risk_level === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{algorithm.algorithm}</div>
                    <div className="text-xs text-muted-foreground">{algorithm.models} models</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Avg Bias: {algorithm.avg_bias}</div>
                    <div className="text-xs text-muted-foreground">Inheritance: {algorithm.inheritance_rate}</div>
                  </div>
                  <Badge variant={algorithm.risk_level === "HIGH" ? "destructive" : "outline"}>
                    {algorithm.risk_level}
                  </Badge>
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
            <CardTitle className="text-sm">DNA SIGNATURE DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">MODEL DNA SIGNATURE PATTERNS</CardDescription>
          </CardHeader>
          <CardContent>
            <DistributionChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">INHERITANCE PERFORMANCE</CardTitle>
            <CardDescription className="text-xs">BIAS INHERITANCE VS PERFORMANCE</CardDescription>
          </CardHeader>
          <CardContent>
            <PerformanceMatrix />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">ALGORITHM FAMILY BIAS</CardTitle>
            <CardDescription className="text-xs">AVERAGE BIAS BY ALGORITHM FAMILY</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {geneticAlgorithms.map((algorithm, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{algorithm.algorithm}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${algorithm.avg_bias * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{algorithm.avg_bias}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
