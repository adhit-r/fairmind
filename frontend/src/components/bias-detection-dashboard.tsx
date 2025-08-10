"use client"

import * as React from "react"
import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  Upload, 
  Play,
  Shield,
  Users,
  TrendingUp,
  BarChart3
} from "lucide-react"
import { BiasDetectionRadar } from "@/components/charts/bias-detection-radar"
import { useBiasAnalysis } from "@/hooks/use-bias-analysis"
import { ErrorBoundary } from "@/components/ui/error-boundary"
import { BiasAnalysisConfig } from "@/types"

export function BiasDetectionDashboard() {
  const {
    models,
    datasets,
    biasAnalysis,
    loading,
    error,
    analyzeBias,
    clearAnalysis,
    autoPopulateFromDataset
  } = useBiasAnalysis();

  const [selectedModel, setSelectedModel] = useState<string>("")
  const [selectedDataset, setSelectedDataset] = useState<string>("")
  const [target, setTarget] = useState("")
  const [features, setFeatures] = useState("")
  const [protectedAttrs, setProtectedAttrs] = useState("")

  // Auto-populate when dataset changes
  React.useEffect(() => {
    if (selectedDataset) {
      const autoData = autoPopulateFromDataset(selectedDataset);
      if (autoData) {
        setFeatures(autoData.features);
        setTarget(autoData.target);
      }
    }
  }, [selectedDataset, autoPopulateFromDataset]);

  const handleRunAnalysis = async () => {
    if (!selectedModel || !selectedDataset || !target || !features) {
      return;
    }

    const config: BiasAnalysisConfig = {
      modelPath: selectedModel,
      datasetPath: selectedDataset,
      target,
      features: features.split(",").map(f => f.trim()),
      protectedAttributes: protectedAttrs.split(",").map(f => f.trim()).filter(Boolean)
    };

    await analyzeBias(config);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case "LOW": return "bg-green-100 text-green-800"
      case "MEDIUM": return "bg-yellow-100 text-yellow-800"
      case "HIGH": return "bg-orange-100 text-orange-800"
      case "CRITICAL": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pass": return <CheckCircle className="h-4 w-4 text-green-600" />
      case "fail": return <XCircle className="h-4 w-4 text-red-600" />
      case "warning": return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      default: return <Info className="h-4 w-4 text-gray-600" />
    }
  }

  const isFormValid = selectedModel && selectedDataset && target && features;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Bias Detection</h1>
          <p className="text-muted-foreground">
            Analyze your AI models for fairness and bias across protected attributes
          </p>
        </div>
        <Badge variant="outline" className="flex items-center gap-2">
          <Shield className="h-4 w-4" />
          AI Fairness Analysis
        </Badge>
      </div>

      {/* Error Boundary */}
      <ErrorBoundary 
        error={error} 
        onRetry={clearAnalysis}
      />

      {/* Input Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Model & Dataset Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Model</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full p-2 border rounded bg-background"
                disabled={loading}
              >
                <option value="">Choose a model...</option>
                {models.map((model) => (
                  <option key={model.id} value={model.path}>
                    {model.name} ({model.framework || 'Unknown'})
                  </option>
                ))}
              </select>
              {models.length === 0 && !loading && (
                <p className="text-xs text-muted-foreground">
                  No models available. Upload a model first.
                </p>
              )}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Dataset</label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full p-2 border rounded bg-background"
                disabled={loading}
              >
                <option value="">Choose a dataset...</option>
                {datasets.map((dataset) => (
                  <option key={dataset.path} value={dataset.path}>
                    {dataset.name} ({dataset.rows} rows, {dataset.columns?.length || 0} cols)
                  </option>
                ))}
              </select>
              {datasets.length === 0 && !loading && (
                <p className="text-xs text-muted-foreground">
                  No datasets available. Upload a dataset first.
                </p>
              )}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Target Column</label>
              <input
                type="text"
                placeholder="target"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                className="w-full p-2 border rounded"
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Feature Columns (comma-separated)</label>
              <input
                type="text"
                placeholder="feature1,feature2,feature3"
                value={features}
                onChange={(e) => setFeatures(e.target.value)}
                className="w-full p-2 border rounded"
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Protected Attributes (comma-separated)</label>
              <input
                type="text"
                placeholder="gender,race,age"
                value={protectedAttrs}
                onChange={(e) => setProtectedAttrs(e.target.value)}
                className="w-full p-2 border rounded"
                disabled={loading}
              />
            </div>
          </div>

          <Button 
            onClick={handleRunAnalysis}
            disabled={loading || !isFormValid}
            className="w-full"
          >
            <Play className="mr-2 h-4 w-4" />
            {loading ? "Analyzing..." : "Run Bias Analysis"}
          </Button>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {biasAnalysis && (
        <div className="space-y-6">
          {/* Overall Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Analysis Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center p-4 border rounded">
                  <div className="text-2xl font-bold">{Math.round(biasAnalysis.overall_score * 100)}%</div>
                  <div className="text-sm text-muted-foreground">Fairness Score</div>
                </div>
                <div className="text-center p-4 border rounded">
                  <Badge className={getRiskColor(biasAnalysis.risk_level)}>
                    {biasAnalysis.risk_level} RISK
                  </Badge>
                  <div className="text-sm text-muted-foreground mt-1">Risk Level</div>
                </div>
                <div className="text-center p-4 border rounded">
                  <div className="text-2xl font-bold">{biasAnalysis.protected_attributes.length}</div>
                  <div className="text-sm text-muted-foreground">Protected Attributes</div>
                </div>
                <div className="text-center p-4 border rounded">
                  <div className="text-2xl font-bold">{biasAnalysis.affected_groups.length}</div>
                  <div className="text-sm text-muted-foreground">Affected Groups</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bias Detection Radar */}
          <Card>
            <CardHeader>
              <CardTitle>Bias Detection Radar</CardTitle>
            </CardHeader>
            <CardContent>
              <BiasDetectionRadar 
                dimensions={biasAnalysis.metrics.map(metric => ({
                  dimension: metric.name.split(" - ")[1] || metric.name,
                  score: metric.value,
                  threshold: metric.threshold,
                  risk_level: metric.value > metric.threshold ? "HIGH" : "LOW"
                }))}
              />
            </CardContent>
          </Card>

          {/* Detailed Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Bias Metrics Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {biasAnalysis.metrics.map((metric, index) => (
                  <div key={index} className="border rounded p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(metric.status)}
                        <span className="font-medium">{metric.name}</span>
                      </div>
                      <Badge variant={metric.status === "pass" ? "default" : "destructive"}>
                        {metric.status.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Value: {metric.value.toFixed(4)}</span>
                        <span>Threshold: {metric.threshold.toFixed(4)}</span>
                      </div>
                      <Progress 
                        value={(metric.value / metric.threshold) * 100} 
                        className="h-2"
                      />
                      <p className="text-sm text-muted-foreground">{metric.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {biasAnalysis.recommendations.length > 0 ? (
                <div className="space-y-2">
                  {biasAnalysis.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start gap-2 p-3 bg-muted rounded">
                      <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                      <p className="text-sm">{rec}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No specific recommendations at this time.</p>
              )}
            </CardContent>
          </Card>

          {/* Affected Groups */}
          {biasAnalysis.affected_groups.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Affected Groups
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {biasAnalysis.affected_groups.map((group, index) => (
                    <Badge key={index} variant="outline">
                      {group}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
