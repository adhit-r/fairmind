"use client"

import { Button } from "@/components/ui/common/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/common/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/common/table"
import { FileText, Shield, Activity, TrendingUp, TrendingDown, Eye, Play, BarChart3, Target, Network, Zap, Clock, CheckCircle, XCircle, AlertTriangle } from "lucide-react"
import { ComplianceTimeline } from "@/components/charts/compliance-timeline"
import { NISTComplianceMatrix } from "@/components/charts/nist-compliance-matrix"

const complianceMetrics = [
  { label: "REQUIREMENTS", value: "15", trend: "+2", icon: FileText },
  { label: "COMPLETED", value: "12", trend: "+3", icon: CheckCircle },
  { label: "PENDING", value: "3", trend: "-1", icon: AlertTriangle },
  { label: "COMPLIANCE SCORE", value: "80%", trend: "+5%", icon: Shield },
]

const aiBillRequirements = [
  { requirement: "TRANSPARENCY DISCLOSURES", status: "COMPLETED", deadline: "2025-08-15", priority: "HIGH", progress: 100, assigned_to: "john.doe" },
  { requirement: "BIAS ASSESSMENT REPORTS", status: "IN PROGRESS", deadline: "2025-08-20", priority: "HIGH", progress: 75, assigned_to: "sarah.smith" },
  { requirement: "HUMAN OVERSIGHT PROTOCOLS", status: "PENDING", deadline: "2025-08-25", priority: "MEDIUM", progress: 25, assigned_to: "mike.jones" },
  { requirement: "IMPACT ASSESSMENT", status: "COMPLETED", deadline: "2025-08-10", priority: "HIGH", progress: 100, assigned_to: "john.doe" },
  { requirement: "SAFEGUARD IMPLEMENTATION", status: "IN PROGRESS", deadline: "2025-08-30", priority: "MEDIUM", progress: 60, assigned_to: "sarah.smith" },
]

const auditTrail = [
  { action: "MODEL DEPLOYMENT", user: "john.doe", timestamp: "2025-08-07 14:30", status: "SUCCESS", model: "LOAN MODEL V1", compliance_check: "PASSED" },
  { action: "BIAS ASSESSMENT", user: "sarah.smith", timestamp: "2025-08-07 13:45", status: "SUCCESS", model: "GPT4 HIRING ASSISTANT", compliance_check: "PASSED" },
  { action: "COMPLIANCE CHECK", user: "mike.jones", timestamp: "2025-08-07 12:20", status: "FAILED", model: "CREDIT SCORING V3", compliance_check: "FAILED" },
  { action: "MODEL UPDATE", user: "john.doe", timestamp: "2025-08-07 11:15", status: "SUCCESS", model: "CLAUDE LEGAL ADVISOR", compliance_check: "PASSED" },
  { action: "DRIFT DETECTION", user: "system", timestamp: "2025-08-07 10:30", status: "WARNING", model: "LOAN MODEL V1", compliance_check: "WARNING" },
]

const regulatoryFrameworks = [
  { framework: "AI BILL", status: "COMPLIANT", score: 85, last_audit: "2025-08-01", next_audit: "2025-09-01", requirements: 15, completed: 12 },
  { framework: "GDPR", status: "COMPLIANT", score: 92, last_audit: "2025-07-15", next_audit: "2025-10-15", requirements: 12, completed: 12 },
  { framework: "CCPA", status: "COMPLIANT", score: 88, last_audit: "2025-07-20", next_audit: "2025-10-20", requirements: 10, completed: 9 },
  { framework: "NIST AI RMF", status: "PENDING", score: 76, last_audit: "2025-08-05", next_audit: "2025-09-05", requirements: 20, completed: 15 },
]

const complianceAlerts = [
  { alert: "DEADLINE APPROACHING", requirement: "BIAS ASSESSMENT REPORTS", days_left: 13, severity: "MEDIUM", assigned_to: "sarah.smith" },
  { alert: "COMPLIANCE FAILURE", requirement: "HUMAN OVERSIGHT PROTOCOLS", days_left: 18, severity: "HIGH", assigned_to: "mike.jones" },
  { alert: "AUDIT DUE", requirement: "NIST AI RMF", days_left: 28, severity: "LOW", assigned_to: "john.doe" },
  { alert: "REQUIREMENT UPDATED", requirement: "SAFEGUARD IMPLEMENTATION", days_left: 23, severity: "MEDIUM", assigned_to: "sarah.smith" },
]

export function ComplianceDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">COMPLIANCE TRACKING</h1>
        <p className="text-sm text-muted-foreground font-mono">
          AI BILL AUDIT TRAILS REGULATORY REQUIREMENT MANAGEMENT
        </p>
      </div>

      {/* Compliance Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {complianceMetrics.map((metric) => (
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
            <FileText className="mr-2 h-4 w-4" />
            RUN COMPLIANCE CHECK
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Activity className="mr-2 h-4 w-4" />
            GENERATE AUDIT REPORT
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Shield className="mr-2 h-4 w-4" />
            UPDATE REQUIREMENTS
          </Button>
        </div>
      </div>

      {/* AI Bill Requirements Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="h-4 w-4" />
            AI/ML BILL COMPLIANCE TRACKING
          </CardTitle>
          <CardDescription className="text-xs">REGULATORY REQUIREMENT MANAGEMENT</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {aiBillRequirements.map((req, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    req.status === "COMPLETED" ? "bg-green-500" :
                    req.status === "IN PROGRESS" ? "bg-yellow-500" : "bg-gray-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{req.requirement}</div>
                    <div className="text-xs text-muted-foreground">Deadline: {req.deadline} • Assigned: {req.assigned_to}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Progress: {req.progress}%</div>
                    <div className="text-xs text-muted-foreground">{req.status}</div>
                  </div>
                  <Badge variant={req.priority === "HIGH" ? "destructive" : "outline"}>
                    {req.priority}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Audit Trail Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Activity className="h-4 w-4" />
            AUDIT TRAIL
          </CardTitle>
          <CardDescription className="text-xs">COMPREHENSIVE ACTIVITY TRACKING</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {auditTrail.map((audit, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    audit.status === "SUCCESS" ? "bg-green-500" :
                    audit.status === "FAILED" ? "bg-red-500" : "bg-yellow-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{audit.action}</div>
                    <div className="text-xs text-muted-foreground">{audit.model} • {audit.user}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={audit.compliance_check === "PASSED" ? "default" : "outline"}>
                    {audit.compliance_check}
                  </Badge>
                  <Badge variant={audit.status === "SUCCESS" ? "default" : "outline"}>
                    {audit.status}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{audit.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Regulatory Frameworks Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Shield className="h-4 w-4" />
            REGULATORY FRAMEWORKS
          </CardTitle>
          <CardDescription className="text-xs">COMPLIANCE STATUS ACROSS FRAMEWORKS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>FRAMEWORK</TableHead>
                  <TableHead>STATUS</TableHead>
                  <TableHead>SCORE</TableHead>
                  <TableHead>REQUIREMENTS</TableHead>
                  <TableHead>LAST AUDIT</TableHead>
                  <TableHead>NEXT AUDIT</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {regulatoryFrameworks.map((framework, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{framework.framework}</div>
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        framework.status === "COMPLIANT" ? "bg-green-100 text-green-800" :
                        framework.status === "PENDING" ? "bg-yellow-100 text-yellow-800" :
                        "bg-red-100 text-red-800"
                      }>
                        {framework.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono">{framework.score}%</TableCell>
                    <TableCell className="font-mono">{framework.completed}/{framework.requirements}</TableCell>
                    <TableCell className="font-mono">{framework.last_audit}</TableCell>
                    <TableCell className="font-mono">{framework.next_audit}</TableCell>
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

      {/* Compliance Alerts Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            COMPLIANCE ALERTS
          </CardTitle>
          <CardDescription className="text-xs">DEADLINES AND REQUIREMENT UPDATES</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {complianceAlerts.map((alert, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`h-4 w-4 ${
                    alert.severity === "HIGH" ? "text-red-500" :
                    alert.severity === "MEDIUM" ? "text-yellow-500" : "text-blue-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{alert.alert}</div>
                    <div className="text-xs text-muted-foreground">{alert.requirement} • {alert.assigned_to}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={alert.severity === "HIGH" ? "destructive" : "outline"}>
                    {alert.severity}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{alert.days_left} days left</span>
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
            <CardTitle className="text-sm">COMPLIANCE TIMELINE</CardTitle>
            <CardDescription className="text-xs">REGULATORY ADHERENCE TRENDS</CardDescription>
          </CardHeader>
          <CardContent>
            <ComplianceTimeline />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">NIST COMPLIANCE MATRIX</CardTitle>
            <CardDescription className="text-xs">REGULATORY COMPLIANCE STATUS</CardDescription>
          </CardHeader>
          <CardContent>
            <NISTComplianceMatrix />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">REQUIREMENT PROGRESS</CardTitle>
            <CardDescription className="text-xs">AI BILL REQUIREMENT COMPLETION</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {aiBillRequirements.map((req, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{req.requirement}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${req.progress}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{req.progress}%</span>
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
