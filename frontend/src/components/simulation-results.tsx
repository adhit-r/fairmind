"use client"

import * as React from "react";
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

// Update chart imports to use relative paths
import { FairnessChart } from "./charts/fairness-chart"
import { RobustnessChart } from "./charts/robustness-chart"
import { PerformanceMatrix } from "./charts/performance-matrix"
import { DistributionChart } from "./charts/distribution-chart"
import { Download, RefreshCw, Flag, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown } from "lucide-react"
import Link from "next/link"


export function SimulationResults() {
  const [fairnessData, setFairnessData] = React.useState<any[]>([]);
  const [robustnessMetrics, setRobustnessMetrics] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch("http://localhost:3001/fairness-summary").then((res) => res.json()),
      fetch("http://localhost:3001/robustness-metrics").then((res) => res.json()),
    ])
      .then(([fairnessRes, robustnessRes]) => {
        setFairnessData(fairnessRes);
        setRobustnessMetrics(robustnessRes);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading simulation results...</div>;
  if (error) return <div className="text-red-500">Error loading results: {error}</div>;
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">SIMULATION_RESULTS: LOAN_MODEL_V1</h1>
          <p className="text-sm text-muted-foreground font-mono">COMPLETED.2025.07.14.23:43 • RUNTIME: 12M.34S</p>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" className="text-xs bg-transparent">
            <Download className="mr-2 h-4 w-4" />
            DOWNLOAD_REPORT
          </Button>
          <Button variant="outline" className="text-xs bg-transparent">
            <RefreshCw className="mr-2 h-4 w-4" />
            RE-RUN
          </Button>
          <Button variant="outline" className="text-xs bg-transparent">
            <Flag className="mr-2 h-4 w-4" />
            FLAG_FOR_REVIEW
          </Button>
        </div>
      </div>

      {/* Critical Alerts */}
      <Alert className="border-yellow-200 bg-yellow-50">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        <AlertTitle className="text-yellow-800">Attention Required</AlertTitle>
        <AlertDescription className="text-yellow-700">
          Potential bias detected in age groups 26-35 and 56+. Consider retraining with balanced data or implementing
          bias mitigation techniques.
        </AlertDescription>
      </Alert>

      {/* Metrics Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs">OVERALL_SCORE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">79/100</div>
            <p className="text-xs text-muted-foreground">NEEDS.IMPROVEMENT</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs">FAIRNESS_SCORE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">78/100</div>
            <p className="text-xs text-muted-foreground">BIAS.DETECTED</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs">ROBUSTNESS_SCORE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">90/100</div>
            <p className="text-xs text-muted-foreground">EXCELLENT.RESILIENCE</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs">EXPLAINABILITY</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">70/100</div>
            <p className="text-xs text-muted-foreground">LIMITED.TRANSPARENCY</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">FAIRNESS_ANALYSIS</CardTitle>
            <CardDescription className="text-xs">BIAS.ACROSS.DEMOGRAPHICS</CardDescription>
          </CardHeader>
          <CardContent>
            <FairnessChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">ROBUSTNESS_METRICS</CardTitle>
            <CardDescription className="text-xs">PERFORMANCE.UNDER.NOISE</CardDescription>
          </CardHeader>
          <CardContent>
            <RobustnessChart />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <PerformanceMatrix />

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">PREDICTION_DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">OUTPUT.SCORE.HISTOGRAM</CardDescription>
          </CardHeader>
          <CardContent>
            <DistributionChart />
          </CardContent>
        </Card>
      </div>

      {/* Detailed Results Tabs */}
      <Tabs defaultValue="fairness" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="fairness">Fairness Analysis</TabsTrigger>
          <TabsTrigger value="robustness">Robustness</TabsTrigger>
          <TabsTrigger value="explainability">Explainability</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        {/* Fairness Tab */}
        <TabsContent value="fairness" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Bias by Age Group</CardTitle>
                <CardDescription>Fairness scores across different age demographics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {fairnessData.map((item) => (
                  <div key={item.group} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.group}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{item.score}%</span>
                        {item.status === "good" ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        )}
                      </div>
                    </div>
                    <Progress
                      value={item.score}
                      className={`h-2 ${item.status === "good" ? "text-green-600" : "text-yellow-600"}`}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Areas Identified</CardTitle>
                <CardDescription>Specific bias patterns detected</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 border rounded-lg bg-yellow-50">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">Age Discrimination</p>
                      <p className="text-xs text-muted-foreground">
                        Applicants aged 26-35 show 15% lower approval rates despite similar credit profiles
                      </p>
                      <Badge variant="outline" className="mt-2">
                        High Priority
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 border rounded-lg bg-yellow-50">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">Senior Applicant Bias</p>
                      <p className="text-xs text-muted-foreground">
                        Applicants over 56 experience inconsistent decision patterns
                      </p>
                      <Badge variant="outline" className="mt-2">
                        Medium Priority
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Robustness Tab */}
        <TabsContent value="robustness" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Robustness Metrics</CardTitle>
                <CardDescription>Model performance under various stress conditions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {robustnessMetrics.map((metric) => (
                  <div key={metric.metric} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium text-sm">{metric.metric}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-lg font-bold text-green-600">{metric.score}%</span>
                        <div className="flex items-center gap-1">
                          {metric.change.startsWith("+") ? (
                            <TrendingUp className="h-3 w-3 text-green-600" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-red-600" />
                          )}
                          <span
                            className={`text-xs ${metric.change.startsWith("+") ? "text-green-600" : "text-red-600"}`}
                          >
                            {metric.change}
                          </span>
                        </div>
                      </div>
                    </div>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Stress Test Results</CardTitle>
                <CardDescription>Performance under adversarial conditions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 border rounded-lg bg-green-50">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">Gaussian Noise (σ=0.1)</span>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Accuracy maintained at 94.2% under noise injection
                    </p>
                  </div>

                  <div className="p-3 border rounded-lg bg-green-50">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">Feature Perturbation</span>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Stable predictions with ±10% feature variation</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Explainability Tab */}
        <TabsContent value="explainability" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Interpretability Analysis</CardTitle>
              <CardDescription>SHAP and LIME analysis results</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Limited Explainability</AlertTitle>
                  <AlertDescription>
                    The model shows complex feature interactions that are difficult to interpret. Consider using simpler
                    models or additional explanation techniques for high-stakes decisions.
                  </AlertDescription>
                </Alert>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">Top Feature Importance</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Credit Score</span>
                        <span className="text-sm font-medium">0.34</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Income</span>
                        <span className="text-sm font-medium">0.28</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Debt-to-Income</span>
                        <span className="text-sm font-medium">0.22</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Employment History</span>
                        <span className="text-sm font-medium">0.16</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">Explanation Quality</h4>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">SHAP Consistency</span>
                          <span className="text-sm">72%</span>
                        </div>
                        <Progress value={72} className="h-2" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">LIME Stability</span>
                          <span className="text-sm">68%</span>
                        </div>
                        <Progress value={68} className="h-2" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="compliance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Regulatory Compliance Check</CardTitle>
              <CardDescription>Adherence to relevant regulations and standards</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="p-4 border rounded-lg bg-green-50">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-medium">GDPR Compliance</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Model meets data protection requirements</p>
                  </div>

                  <div className="p-4 border rounded-lg bg-yellow-50">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <span className="font-medium">Fair Credit Reporting Act</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Potential issues with adverse action explanations</p>
                  </div>

                  <div className="p-4 border rounded-lg bg-green-50">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-medium">Equal Credit Opportunity Act</span>
                    </div>
                    <p className="text-sm text-muted-foreground">No prohibited basis discrimination detected</p>
                  </div>

                  <div className="p-4 border rounded-lg bg-red-50">
                    <div className="flex items-center gap-2 mb-2">
                      <XCircle className="h-5 w-5 text-red-600" />
                      <span className="font-medium">Fair Housing Act</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Age-based disparities may violate regulations</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <Link href="/">
          <Button variant="outline">Back to Dashboard</Button>
        </Link>

        <div className="flex gap-2">
          <Button variant="outline">Export Data</Button>
          <Button variant="outline">Schedule Re-test</Button>
          <Link href="/simulation/new">
            <Button className="bg-blue-600 hover:bg-blue-700">Run New Simulation</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
