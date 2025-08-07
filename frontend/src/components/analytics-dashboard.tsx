"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, TrendingUp, TrendingDown, Eye, Play, Target, Network, Zap, Activity, Brain, Shield, FileText } from "lucide-react"
import { AIGovernanceChart } from "@/components/charts/ai-governance-chart"
import { BiasDetectionRadar } from "@/components/charts/bias-detection-radar"
import { ModelLifecycleChart } from "@/components/charts/model-lifecycle-chart"
import { RiskHeatmap } from "@/components/charts/risk-heatmap"
import { LLMSafetyDashboard } from "@/components/charts/llm-safety-dashboard"
import { ExplainabilityTreemap } from "@/components/charts/explainability-treemap"

const analyticsMetrics = [
  { label: "CHARTS", value: "12", trend: "+2", icon: BarChart3 },
  { label: "DATASETS", value: "8", trend: "+1", icon: Network },
  { label: "INSIGHTS", value: "24", trend: "+5", icon: Brain },
  { label: "VISUALIZATIONS", value: "18", trend: "+3", icon: Target },
]

const analyticsInsights = [
  { insight: "BIAS CORRELATION DETECTED", model: "LOAN MODEL V1", confidence: 0.92, impact: "HIGH", category: "BIAS_ANALYSIS" },
  { insight: "PERFORMANCE DEGRADATION TREND", model: "GPT4 HIRING ASSISTANT", confidence: 0.85, impact: "MEDIUM", category: "PERFORMANCE" },
  { insight: "COMPLIANCE GAP IDENTIFIED", model: "CREDIT SCORING V3", confidence: 0.78, impact: "HIGH", category: "COMPLIANCE" },
  { insight: "DRIFT PATTERN EMERGING", model: "CLAUDE LEGAL ADVISOR", confidence: 0.89, impact: "MEDIUM", category: "DRIFT" },
]

const dataSources = [
  { source: "MODEL PREDICTIONS", records: 15420, last_updated: "2 min ago", status: "ACTIVE", quality_score: 0.95 },
  { source: "BIAS ASSESSMENTS", records: 8920, last_updated: "5 min ago", status: "ACTIVE", quality_score: 0.88 },
  { source: "COMPLIANCE CHECKS", records: 6340, last_updated: "10 min ago", status: "ACTIVE", quality_score: 0.92 },
  { source: "DRIFT DETECTION", records: 4560, last_updated: "15 min ago", status: "ACTIVE", quality_score: 0.87 },
]

const visualizationTypes = [
  { type: "BIAS RADAR", models: 8, last_used: "2 min ago", complexity: "MEDIUM", status: "ACTIVE" },
  { type: "PERFORMANCE MATRIX", models: 12, last_used: "5 min ago", complexity: "HIGH", status: "ACTIVE" },
  { type: "COMPLIANCE TIMELINE", models: 6, last_used: "8 min ago", complexity: "LOW", status: "ACTIVE" },
  { type: "DRIFT MONITOR", models: 10, last_used: "12 min ago", complexity: "MEDIUM", status: "ACTIVE" },
]

export function AnalyticsDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">ANALYTICS DASHBOARD</h1>
        <p className="text-sm text-muted-foreground font-mono">
          CHARTS VISUALIZATIONS METRICS INSIGHTS
        </p>
      </div>

      {/* Analytics Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {analyticsMetrics.map((metric) => (
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
            <BarChart3 className="mr-2 h-4 w-4" />
            GENERATE INSIGHTS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Network className="mr-2 h-4 w-4" />
            EXPORT DATA
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Target className="mr-2 h-4 w-4" />
            CREATE VISUALIZATION
          </Button>
        </div>
      </div>

      {/* Analytics Insights Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Brain className="h-4 w-4" />
            ANALYTICS INSIGHTS
          </CardTitle>
          <CardDescription className="text-xs">AI-GENERATED INSIGHTS AND PATTERNS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analyticsInsights.map((insight, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    insight.impact === "HIGH" ? "bg-red-500" :
                    insight.impact === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{insight.insight}</div>
                    <div className="text-xs text-muted-foreground">{insight.model} • {insight.category}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Confidence: {insight.confidence}</div>
                    <div className="text-xs text-muted-foreground">AI Generated</div>
                  </div>
                  <Badge variant={insight.impact === "HIGH" ? "destructive" : "outline"}>
                    {insight.impact}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Data Sources Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Network className="h-4 w-4" />
            DATA SOURCES
          </CardTitle>
          <CardDescription className="text-xs">ANALYTICS DATA SOURCES AND QUALITY</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {dataSources.map((source, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <div>
                    <div className="font-medium text-sm">{source.source}</div>
                    <div className="text-xs text-muted-foreground">{source.records.toLocaleString()} records</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Quality: {source.quality_score}</div>
                    <div className="text-xs text-muted-foreground">{source.last_updated}</div>
                  </div>
                  <Badge className="bg-green-100 text-green-800">
                    {source.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Visualization Types Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Target className="h-4 w-4" />
            VISUALIZATION TYPES
          </CardTitle>
          <CardDescription className="text-xs">CHART TYPES AND USAGE PATTERNS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {visualizationTypes.map((viz, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                  <div>
                    <div className="font-medium text-sm">{viz.type}</div>
                    <div className="text-xs text-muted-foreground">{viz.models} models</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">{viz.complexity}</div>
                    <div className="text-xs text-muted-foreground">{viz.last_used}</div>
                  </div>
                  <Badge className="bg-green-100 text-green-800">
                    {viz.status}
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
            <CardTitle className="text-sm">AI GOVERNANCE METRICS</CardTitle>
            <CardDescription className="text-xs">FAIRNESS ROBUSTNESS EXPLAINABILITY</CardDescription>
          </CardHeader>
          <CardContent>
            <AIGovernanceChart />
          </CardContent>
        </Card>

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
            <CardTitle className="text-sm">MODEL LIFECYCLE</CardTitle>
            <CardDescription className="text-xs">DEVELOPMENT TO DEPLOYMENT METRICS</CardDescription>
          </CardHeader>
          <CardContent>
            <ModelLifecycleChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">RISK HEATMAP</CardTitle>
            <CardDescription className="text-xs">MODEL RISK VISUALIZATION</CardDescription>
          </CardHeader>
          <CardContent>
            <RiskHeatmap />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">LLM SAFETY ASSESSMENT</CardTitle>
            <CardDescription className="text-xs">TOXICITY BIAS HALLUCINATION</CardDescription>
          </CardHeader>
          <CardContent>
            <LLMSafetyDashboard />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">EXPLAINABILITY TREEMAP</CardTitle>
            <CardDescription className="text-xs">MODEL INTERPRETABILITY ANALYSIS</CardDescription>
          </CardHeader>
          <CardContent>
            <ExplainabilityTreemap />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
