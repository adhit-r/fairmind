"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Network, Brain, TrendingUp, TrendingDown, Eye, Play, BarChart3, Target, Zap, Activity, Database, GitBranch, AlertTriangle } from "lucide-react"
import { BiasDetectionRadar } from "@/components/charts/bias-detection-radar"
import { DistributionChart } from "@/components/charts/distribution-chart"

const knowledgeGraphMetrics = [
  { label: "GRAPH NODES", value: "2,847", trend: "+156", icon: Network },
  { label: "RELATIONSHIPS", value: "5,234", trend: "+234", icon: Brain },
  { label: "BIAS PATTERNS", value: "89", trend: "+12", icon: AlertTriangle },
  { label: "CAUSAL CHAINS", value: "156", trend: "+23", icon: Database },
]

const neo4jConnection = {
  status: "CONNECTED",
  url: "neo4j://localhost:7687",
  database: "fairmind",
  nodes: 2847,
  relationships: 5234,
  queries_per_second: 45,
  memory_usage: "2.3GB"
}

const biasPatterns = [
  { pattern: "GENDER_BIAS_PROPAGATION", nodes: 45, relationships: 89, confidence: 0.92, impact: "HIGH", source: "HIRING_MODEL" },
  { pattern: "RACIAL_BIAS_CASCADE", nodes: 32, relationships: 67, confidence: 0.88, impact: "HIGH", source: "LOAN_MODEL" },
  { pattern: "AGE_DISCRIMINATION_CHAIN", nodes: 28, relationships: 54, confidence: 0.85, impact: "MEDIUM", source: "INSURANCE_MODEL" },
  { pattern: "GEOGRAPHIC_BIAS_SPREAD", nodes: 38, relationships: 76, confidence: 0.90, impact: "HIGH", source: "CREDIT_MODEL" },
]

const causalRelationships = [
  { source: "EDUCATION_LEVEL", target: "INCOME", relationship: "CORRELATES_WITH", bias_contribution: 0.25, confidence: 0.89 },
  { source: "ZIP_CODE", target: "CREDIT_SCORE", relationship: "INFLUENCES", bias_contribution: 0.32, confidence: 0.92 },
  { source: "GENDER", target: "HIRING_DECISION", relationship: "DISCRIMINATES", bias_contribution: 0.18, confidence: 0.85 },
  { source: "AGE", target: "INSURANCE_PREMIUM", relationship: "AFFECTS", bias_contribution: 0.15, confidence: 0.78 },
]

const cypherQueries = [
  { query: "MATCH (n:BiasPattern)-[:PROPAGATES_TO]->(m:Model) RETURN n, m", description: "Find bias propagation patterns", execution_time: "45ms", results: 23 },
  { query: "MATCH (f:Feature)-[:INFLUENCES]->(d:Decision) WHERE f.bias_score > 0.1 RETURN f, d", description: "High bias feature detection", execution_time: "32ms", results: 15 },
  { query: "MATCH path = (s:Source)-[:CAUSES*1..3]->(t:Target) RETURN path", description: "Multi-hop causal chains", execution_time: "67ms", results: 8 },
  { query: "MATCH (m:Model)-[:HAS_BIAS]->(b:Bias) WHERE b.severity = 'HIGH' RETURN m, b", description: "High severity bias models", execution_time: "28ms", results: 12 },
]

const graphAlerts = [
  { alert: "BIAS CASCADE DETECTED", pattern: "GENDER_BIAS_PROPAGATION", severity: "HIGH", time: "2 min ago", affected_models: 3 },
  { alert: "NEW CAUSAL RELATIONSHIP", pattern: "EDUCATION_INCOME_CORRELATION", severity: "MEDIUM", time: "5 min ago", affected_models: 2 },
  { alert: "BIAS AMPLIFICATION", pattern: "RACIAL_BIAS_CASCADE", severity: "HIGH", time: "8 min ago", affected_models: 4 },
  { alert: "GRAPH PATTERN EMERGING", pattern: "AGE_DISCRIMINATION_CHAIN", severity: "MEDIUM", time: "12 min ago", affected_models: 1 },
]

export function KnowledgeGraphDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">KNOWLEDGE GRAPH ANALYSIS</h1>
        <p className="text-sm text-muted-foreground font-mono">
          NEO4J INTEGRATION CAUSAL RELATIONSHIPS BIAS PROPAGATION PATTERNS
        </p>
      </div>

      {/* Knowledge Graph Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {knowledgeGraphMetrics.map((metric) => (
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
            <Database className="mr-2 h-4 w-4" />
            CONNECT TO NEO4J
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Network className="mr-2 h-4 w-4" />
            UPDATE GRAPH
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Brain className="mr-2 h-4 w-4" />
            RUN GRAPH QUERIES
          </Button>
        </div>
      </div>

      {/* Neo4j Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Database className="h-4 w-4" />
            NEO4J CONNECTION STATUS
          </CardTitle>
          <CardDescription className="text-xs">GRAPH DATABASE CONNECTION AND METRICS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${neo4jConnection.status === "CONNECTED" ? "bg-green-500" : "bg-red-500"}`} />
                <div>
                  <div className="font-medium text-sm">Neo4j Database</div>
                  <div className="text-xs text-muted-foreground">{neo4jConnection.url}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="text-sm font-mono">{neo4jConnection.nodes} nodes</div>
                  <div className="text-xs text-muted-foreground">{neo4jConnection.relationships} relationships</div>
                </div>
                <Badge className={neo4jConnection.status === "CONNECTED" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                  {neo4jConnection.status}
                </Badge>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="font-mono">{neo4jConnection.queries_per_second}</div>
                <div className="text-xs text-muted-foreground">Queries/sec</div>
              </div>
              <div className="text-center">
                <div className="font-mono">{neo4jConnection.memory_usage}</div>
                <div className="text-xs text-muted-foreground">Memory Usage</div>
              </div>
              <div className="text-center">
                <div className="font-mono">{neo4jConnection.database}</div>
                <div className="text-xs text-muted-foreground">Database</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bias Patterns Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            BIAS PATTERNS IN GRAPH
          </CardTitle>
          <CardDescription className="text-xs">DETECTED BIAS PATTERNS AND PROPAGATION CHAINS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>PATTERN</TableHead>
                  <TableHead>NODES</TableHead>
                  <TableHead>RELATIONSHIPS</TableHead>
                  <TableHead>CONFIDENCE</TableHead>
                  <TableHead>IMPACT</TableHead>
                  <TableHead>SOURCE</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {biasPatterns.map((pattern, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{pattern.pattern}</div>
                    </TableCell>
                    <TableCell className="font-mono">{pattern.nodes}</TableCell>
                    <TableCell className="font-mono">{pattern.relationships}</TableCell>
                    <TableCell className="font-mono">{pattern.confidence}</TableCell>
                    <TableCell>
                      <Badge variant={pattern.impact === "HIGH" ? "destructive" : "outline"}>
                        {pattern.impact}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono">{pattern.source}</TableCell>
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

      {/* Causal Relationships Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Network className="h-4 w-4" />
            CAUSAL RELATIONSHIPS
          </CardTitle>
          <CardDescription className="text-xs">CAUSAL CHAINS AND BIAS CONTRIBUTION</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {causalRelationships.map((relationship, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    relationship.bias_contribution > 0.25 ? "bg-red-500" :
                    relationship.bias_contribution > 0.15 ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{relationship.source} → {relationship.target}</div>
                    <div className="text-xs text-muted-foreground">{relationship.relationship}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Bias: {relationship.bias_contribution}</div>
                    <div className="text-xs text-muted-foreground">Confidence: {relationship.confidence}</div>
                  </div>
                  <Badge variant={relationship.bias_contribution > 0.25 ? "destructive" : "outline"}>
                    {relationship.bias_contribution > 0.25 ? "HIGH" : relationship.bias_contribution > 0.15 ? "MEDIUM" : "LOW"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cypher Queries Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Brain className="h-4 w-4" />
            CYPHER QUERIES
          </CardTitle>
          <CardDescription className="text-xs">GRAPH QUERIES FOR BIAS DETECTION</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {cypherQueries.map((query, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  <div>
                    <div className="font-medium text-sm">{query.description}</div>
                    <div className="text-xs text-muted-foreground font-mono">{query.query}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">{query.execution_time}</div>
                    <div className="text-xs text-muted-foreground">{query.results} results</div>
                  </div>
                  <Button size="sm" variant="outline">
                    <Play className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Graph Alerts Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            GRAPH ALERTS
          </CardTitle>
          <CardDescription className="text-xs">REAL-TIME GRAPH PATTERN DETECTION</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {graphAlerts.map((alert, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`h-4 w-4 ${
                    alert.severity === "HIGH" ? "text-red-500" :
                    alert.severity === "MEDIUM" ? "text-yellow-500" : "text-blue-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{alert.alert}</div>
                    <div className="text-xs text-muted-foreground">{alert.pattern} • {alert.affected_models} models</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={alert.severity === "HIGH" ? "destructive" : "outline"}>
                    {alert.severity}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{alert.time}</span>
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
            <CardDescription className="text-xs">GRAPH-BASED BIAS ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent>
            <BiasDetectionRadar />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">GRAPH DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">NODE AND RELATIONSHIP DISTRIBUTION</CardDescription>
          </CardHeader>
          <CardContent>
            <DistributionChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">BIAS PATTERN CONFIDENCE</CardTitle>
            <CardDescription className="text-xs">CONFIDENCE SCORES FOR DETECTED PATTERNS</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {biasPatterns.map((pattern, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{pattern.pattern}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${pattern.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{pattern.confidence}</span>
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
