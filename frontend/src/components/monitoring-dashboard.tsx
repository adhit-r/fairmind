"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Bell, Activity, AlertTriangle, TrendingUp, TrendingDown, Eye, Play, BarChart3, Target, Network, Zap, Clock, Settings } from "lucide-react"
import { ModelDriftMonitor } from "@/components/charts/model-drift-monitor"
import { ComplianceTimeline } from "@/components/charts/compliance-timeline"

const monitoringMetrics = [
  { label: "ACTIVE ALERTS", value: "8", trend: "+2", icon: Bell },
  { label: "DRIFT EVENTS", value: "3", trend: "-1", icon: AlertTriangle },
  { label: "PERFORMANCE ISSUES", value: "5", trend: "+1", icon: Activity },
  { label: "MONITORED MODELS", value: "47", trend: "+3", icon: Network },
]

const liveAlerts = [
  { alert: "DRIFT DETECTED", model: "LOAN MODEL V1", severity: "MEDIUM", time: "2 min ago", status: "INVESTIGATING", drift_score: 0.15 },
  { alert: "BIAS THRESHOLD EXCEEDED", model: "GPT4 HIRING ASSISTANT", severity: "HIGH", time: "5 min ago", status: "MITIGATING", drift_score: 0.32 },
  { alert: "COMPLIANCE DEADLINE", model: "CREDIT SCORING V3", severity: "LOW", time: "10 min ago", status: "MONITORING", drift_score: 0.08 },
  { alert: "PERFORMANCE DEGRADATION", model: "CLAUDE LEGAL ADVISOR", severity: "MEDIUM", time: "15 min ago", status: "RESOLVED", drift_score: 0.22 },
  { alert: "MODEL FAILURE", model: "FRAUD DETECTION V2", severity: "HIGH", time: "20 min ago", status: "INVESTIGATING", drift_score: 0.45 },
]

const driftEvents = [
  { model: "LOAN MODEL V1", drift_type: "DATA DRIFT", severity: "MEDIUM", detected_at: "2 min ago", impact: "LOW", confidence: 0.85 },
  { model: "GPT4 HIRING ASSISTANT", drift_type: "CONCEPT DRIFT", severity: "HIGH", detected_at: "5 min ago", impact: "HIGH", confidence: 0.92 },
  { model: "CREDIT SCORING V3", drift_type: "FEATURE DRIFT", severity: "LOW", detected_at: "10 min ago", impact: "MEDIUM", confidence: 0.78 },
  { model: "CLAUDE LEGAL ADVISOR", drift_type: "LABEL DRIFT", severity: "MEDIUM", detected_at: "15 min ago", impact: "LOW", confidence: 0.81 },
]

const performanceIssues = [
  { model: "LOAN MODEL V1", issue: "ACCURACY DROP", metric: "ACCURACY", current: 0.85, expected: 0.92, threshold: 0.90, status: "WARNING" },
  { model: "GPT4 HIRING ASSISTANT", issue: "LATENCY INCREASE", metric: "LATENCY", current: 2.5, expected: 1.8, threshold: 2.0, status: "CRITICAL" },
  { model: "CREDIT SCORING V3", issue: "THROUGHPUT DECREASE", metric: "THROUGHPUT", current: 150, expected: 200, threshold: 180, status: "WARNING" },
  { model: "CLAUDE LEGAL ADVISOR", issue: "MEMORY USAGE", metric: "MEMORY", current: 85, expected: 70, threshold: 80, status: "CRITICAL" },
]

const monitoringConfig = [
  { model: "LOAN MODEL V1", monitoring_enabled: true, drift_threshold: 0.15, bias_threshold: 0.10, performance_threshold: 0.90, alerts_enabled: true },
  { model: "GPT4 HIRING ASSISTANT", monitoring_enabled: true, drift_threshold: 0.20, bias_threshold: 0.15, performance_threshold: 0.85, alerts_enabled: true },
  { model: "CREDIT SCORING V3", monitoring_enabled: false, drift_threshold: 0.12, bias_threshold: 0.08, performance_threshold: 0.95, alerts_enabled: false },
  { model: "CLAUDE LEGAL ADVISOR", monitoring_enabled: true, drift_threshold: 0.18, bias_threshold: 0.12, performance_threshold: 0.88, alerts_enabled: true },
]

export function MonitoringDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">REAL-TIME MONITORING</h1>
        <p className="text-sm text-muted-foreground font-mono">
          LIVE ALERTS DRIFT DETECTION PERFORMANCE MONITORING
        </p>
      </div>

      {/* Monitoring Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {monitoringMetrics.map((metric) => (
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
            <Bell className="mr-2 h-4 w-4" />
            ACKNOWLEDGE ALL ALERTS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Activity className="mr-2 h-4 w-4" />
            RUN DRIFT ANALYSIS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <BarChart3 className="mr-2 h-4 w-4" />
            PERFORMANCE REPORT
          </Button>
        </div>
      </div>

      {/* Live Alerts Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Bell className="h-4 w-4" />
            LIVE ALERTS
          </CardTitle>
          <CardDescription className="text-xs">REAL-TIME MONITORING AND NOTIFICATIONS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {liveAlerts.map((alert, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`h-4 w-4 ${
                    alert.severity === "HIGH" ? "text-red-500" :
                    alert.severity === "MEDIUM" ? "text-yellow-500" : "text-blue-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{alert.alert}</div>
                    <div className="text-xs text-muted-foreground">{alert.model} • Drift: {alert.drift_score}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={alert.severity === "HIGH" ? "destructive" : "outline"}>
                    {alert.severity}
                  </Badge>
                  <Badge variant="outline">{alert.status}</Badge>
                  <span className="text-xs text-muted-foreground">{alert.time}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Drift Events Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            DRIFT EVENTS
          </CardTitle>
          <CardDescription className="text-xs">MODEL DRIFT DETECTION AND ANALYSIS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>MODEL</TableHead>
                  <TableHead>DRIFT TYPE</TableHead>
                  <TableHead>SEVERITY</TableHead>
                  <TableHead>IMPACT</TableHead>
                  <TableHead>CONFIDENCE</TableHead>
                  <TableHead>DETECTED</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {driftEvents.map((event, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{event.model}</div>
                    </TableCell>
                    <TableCell className="font-mono">{event.drift_type}</TableCell>
                    <TableCell>
                      <Badge className={
                        event.severity === "HIGH" ? "bg-red-100 text-red-800" :
                        event.severity === "MEDIUM" ? "bg-yellow-100 text-yellow-800" :
                        "bg-green-100 text-green-800"
                      }>
                        {event.severity}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{event.impact}</Badge>
                    </TableCell>
                    <TableCell className="font-mono">{event.confidence}</TableCell>
                    <TableCell className="font-mono">{event.detected_at}</TableCell>
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

      {/* Performance Issues Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Activity className="h-4 w-4" />
            PERFORMANCE ISSUES
          </CardTitle>
          <CardDescription className="text-xs">MODEL PERFORMANCE MONITORING AND ALERTS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {performanceIssues.map((issue, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    issue.status === "CRITICAL" ? "bg-red-500" :
                    issue.status === "WARNING" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{issue.model} - {issue.issue}</div>
                    <div className="text-xs text-muted-foreground">{issue.metric}: {issue.current} vs {issue.expected}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Threshold: {issue.threshold}</div>
                    <div className="text-xs text-muted-foreground">{issue.metric} metric</div>
                  </div>
                  <Badge variant={issue.status === "CRITICAL" ? "destructive" : "outline"}>
                    {issue.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Monitoring Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Settings className="h-4 w-4" />
            MONITORING CONFIGURATION
          </CardTitle>
          <CardDescription className="text-xs">MODEL MONITORING SETTINGS AND THRESHOLDS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>MODEL</TableHead>
                  <TableHead>MONITORING</TableHead>
                  <TableHead>DRIFT THRESHOLD</TableHead>
                  <TableHead>BIAS THRESHOLD</TableHead>
                  <TableHead>PERFORMANCE THRESHOLD</TableHead>
                  <TableHead>ALERTS</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {monitoringConfig.map((config, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{config.model}</div>
                    </TableCell>
                    <TableCell>
                      <Badge className={config.monitoring_enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                        {config.monitoring_enabled ? "ENABLED" : "DISABLED"}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono">{config.drift_threshold}</TableCell>
                    <TableCell className="font-mono">{config.bias_threshold}</TableCell>
                    <TableCell className="font-mono">{config.performance_threshold}</TableCell>
                    <TableCell>
                      <Badge className={config.alerts_enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                        {config.alerts_enabled ? "ENABLED" : "DISABLED"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button size="sm" variant="outline">
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Eye className="h-4 w-4" />
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

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">MODEL DRIFT MONITOR</CardTitle>
            <CardDescription className="text-xs">REAL-TIME DRIFT DETECTION</CardDescription>
          </CardHeader>
          <CardContent>
            <ModelDriftMonitor />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">COMPLIANCE TIMELINE</CardTitle>
            <CardDescription className="text-xs">REGULATORY ADHERENCE TRENDS</CardDescription>
          </CardHeader>
          <CardContent>
            <ComplianceTimeline />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">ALERT FREQUENCY</CardTitle>
            <CardDescription className="text-xs">ALERT PATTERNS OVER TIME</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {liveAlerts.map((alert, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{alert.alert}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${alert.drift_score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{alert.drift_score}</span>
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
