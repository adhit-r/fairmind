"use client"

import { useState, useEffect } from 'react'
import { fairmindAPI } from '@/lib/fairmind-api'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { 
  Package, 
  Database, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Code,
  FileText,
  Download,
  Upload,
  Search,
  BarChart3,
  PieChart,
  TrendingUp,
  Activity
} from "lucide-react"

interface ComprehensiveAIBOMData {
  aibom_version: string
  metadata: {
    created: string
    creator: string
    description: string
    scan_type: string
    scan_duration: number
  }
  model_inventory: {
    total_models: number
    model_types: string[]
    total_size: number
  }
  data_inventory: {
    total_datasets: number
    dataset_types: string[]
    total_size: number
  }
  dependency_analysis: {
    total_dependencies: number
    framework_count: number
    license_compliance: {
      compliant: number
      non_compliant: number
      pending: number
    }
  }
  security_analysis: {
    total_vulnerabilities: number
    critical_vulnerabilities: number
    high_vulnerabilities: number
    vulnerability_sources: string[]
  }
  risk_assessment: {
    overall_risk: string
    risk_factors: string[]
    risk_score: number
    risk_level: string
  }
  compliance_status: {
    eu_ai_act: string
    nist_rmf: string
    gdpr: string
    missing_requirements: string[]
  }
  recommendations: string[]
  reproducibility: {
    environment_defined: boolean
    training_scripts_available: boolean
    model_weights_stored: boolean
    configuration_documented: boolean
    reproducibility_score: number
  }
}

export function ComprehensiveAIBOMDashboard() {
  const [projectPath, setProjectPath] = useState('')
  const [aibomData, setAibomData] = useState<ComprehensiveAIBOMData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  const handleGenerateAIBOM = async () => {
    if (!projectPath.trim()) {
      setError('Please enter a project path')
      return
    }

    try {
      setGenerating(true)
      setError(null)
      
      const result = await fairmindAPI.generateComprehensiveAIBOM({
        project_path: projectPath,
        scan_type: 'comprehensive',
        include_dev_dependencies: true,
        include_transitive: true
      })
      
      if (result.success && result.data.comprehensive_analysis) {
        setAibomData(result.data.comprehensive_analysis)
      }
    } catch (error) {
      setError('Failed to generate comprehensive AIBOM')
      console.error('Error generating AIBOM:', error)
    } finally {
      setGenerating(false)
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getComplianceColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'compliant': return 'bg-green-100 text-green-800'
      case 'partially_compliant': return 'bg-yellow-100 text-yellow-800'
      case 'non_compliant': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return <CheckCircle className="h-4 w-4" />
      case 'medium': return <AlertTriangle className="h-4 w-4" />
      case 'high': return <AlertTriangle className="h-4 w-4" />
      case 'critical': return <AlertTriangle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Comprehensive AIBOM Dashboard</h2>
          <p className="text-muted-foreground">
            Generate and analyze comprehensive AI/ML Bill of Materials with advanced insights
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
          <Button variant="outline" size="sm">
            <BarChart3 className="mr-2 h-4 w-4" />
            View Analytics
          </Button>
        </div>
      </div>

      {/* Generate AIBOM Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Generate Comprehensive AIBOM</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <Label htmlFor="project-path">Project Path</Label>
              <Input
                id="project-path"
                placeholder="/path/to/your/ai-project"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
              />
            </div>
            <Button 
              onClick={handleGenerateAIBOM} 
              disabled={generating || !projectPath.trim()}
              className="mt-6"
            >
              {generating ? 'Generating...' : 'Generate AIBOM'}
            </Button>
          </div>
          {error && (
            <Alert className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {aibomData && (
        <>
          {/* Overview Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Components</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {aibomData.dependency_analysis.total_dependencies + 
                   aibomData.model_inventory.total_models + 
                   aibomData.data_inventory.total_datasets}
                </div>
                <p className="text-xs text-muted-foreground">
                  Dependencies, Models & Datasets
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Security Risk</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {aibomData.security_analysis.critical_vulnerabilities + 
                   aibomData.security_analysis.high_vulnerabilities}
                </div>
                <p className="text-xs text-muted-foreground">
                  Critical & High Vulnerabilities
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Overall Risk</CardTitle>
                {getRiskIcon(aibomData.risk_assessment.overall_risk)}
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {aibomData.risk_assessment.risk_score}/10
                </div>
                <Badge className={getRiskColor(aibomData.risk_assessment.overall_risk)}>
                  {aibomData.risk_assessment.overall_risk}
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Reproducibility</CardTitle>
                <Code className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {aibomData.reproducibility.reproducibility_score}/10
                </div>
                <p className="text-xs text-muted-foreground">
                  Reproducibility Score
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Model & Data Inventory */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Model & Data Inventory</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">AI Models</span>
                  <Badge variant="outline">{aibomData.model_inventory.total_models}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Datasets</span>
                  <Badge variant="outline">{aibomData.data_inventory.total_datasets}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Size</span>
                  <span className="text-sm text-muted-foreground">
                    {(aibomData.model_inventory.total_size + aibomData.data_inventory.total_size).toFixed(2)} MB
                  </span>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Model Types</Label>
                  <div className="flex flex-wrap gap-1">
                    {aibomData.model_inventory.model_types.map((type, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Security Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Security Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Critical Vulnerabilities</span>
                    <Badge variant="destructive">{aibomData.security_analysis.critical_vulnerabilities}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">High Vulnerabilities</span>
                    <Badge variant="destructive">{aibomData.security_analysis.high_vulnerabilities}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Total Vulnerabilities</span>
                    <Badge variant="outline">{aibomData.security_analysis.total_vulnerabilities}</Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Vulnerability Sources</Label>
                  <div className="flex flex-wrap gap-1">
                    {aibomData.security_analysis.vulnerability_sources.map((source, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {source}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Compliance Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Compliance Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">EU AI Act</span>
                    <Badge className={getComplianceColor(aibomData.compliance_status.eu_ai_act)}>
                      {aibomData.compliance_status.eu_ai_act}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">NIST RMF</span>
                    <Badge className={getComplianceColor(aibomData.compliance_status.nist_rmf)}>
                      {aibomData.compliance_status.nist_rmf}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">GDPR</span>
                    <Badge className={getComplianceColor(aibomData.compliance_status.gdpr)}>
                      {aibomData.compliance_status.gdpr}
                    </Badge>
                  </div>
                </div>
                {aibomData.compliance_status.missing_requirements.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Missing Requirements</Label>
                    <ul className="text-xs text-muted-foreground space-y-1">
                      {aibomData.compliance_status.missing_requirements.map((req, index) => (
                        <li key={index}>• {req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Risk Assessment */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Risk Score</span>
                    <span className="text-sm font-bold">{aibomData.risk_assessment.risk_score}/10</span>
                  </div>
                  <Progress value={aibomData.risk_assessment.risk_score * 10} className="w-full" />
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Risk Factors</Label>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {aibomData.risk_assessment.risk_factors.map((factor, index) => (
                      <li key={index}>• {factor}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {aibomData.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-muted rounded-lg">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                    <p className="text-sm">{recommendation}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Reproducibility Assessment */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Reproducibility Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2 ${
                    aibomData.reproducibility.environment_defined ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {aibomData.reproducibility.environment_defined ? (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    )}
                  </div>
                  <p className="text-xs font-medium">Environment</p>
                </div>
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2 ${
                    aibomData.reproducibility.training_scripts_available ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {aibomData.reproducibility.training_scripts_available ? (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    )}
                  </div>
                  <p className="text-xs font-medium">Training Scripts</p>
                </div>
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2 ${
                    aibomData.reproducibility.model_weights_stored ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {aibomData.reproducibility.model_weights_stored ? (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    )}
                  </div>
                  <p className="text-xs font-medium">Model Weights</p>
                </div>
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2 ${
                    aibomData.reproducibility.configuration_documented ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {aibomData.reproducibility.configuration_documented ? (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    )}
                  </div>
                  <p className="text-xs font-medium">Configuration</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
