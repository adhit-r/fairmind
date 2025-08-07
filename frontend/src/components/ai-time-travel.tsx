"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface HistoricalScenario {
  scenario_id: string
  name: string
  description: string
  time_period: string
  historical_context: any
  data_characteristics: any
  bias_characteristics: any
  ethical_framework: any
}

interface ModelBehaviorAnalysis {
  model_id: string
  scenario_id: string
  historical_performance: any
  bias_evolution: any
  ethical_assessment: any
  risk_analysis: any
  recommendations: string[]
}

interface BiasEvolution {
  bias_type: string
  historical_value: number
  current_value: number
  change_magnitude: number
  change_direction: string
  historical_context: string
  modern_context: string
}

const timePeriodColors = {
  "1960s": "bg-red-100 text-red-800",
  "1990s": "bg-yellow-100 text-yellow-800",
  "2010s": "bg-blue-100 text-blue-800"
}

export function AITimeTravel() {
  const [scenarios, setScenarios] = useState<HistoricalScenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string>("")
  const [analysis, setAnalysis] = useState<ModelBehaviorAnalysis | null>(null)
  const [biasEvolution, setBiasEvolution] = useState<BiasEvolution[]>([])
  const [performanceComparisons, setPerformanceComparisons] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    model_id: "",
    bias_characteristics: {
      gender_bias: "",
      racial_bias: "",
      age_bias: "",
      socioeconomic_bias: ""
    },
    performance_metrics: {
      accuracy: "",
      precision: "",
      recall: "",
      f1_score: ""
    }
  })

  const loadScenarios = async () => {
    try {
      const response = await fetch("http://localhost:8000/time-travel/scenarios")
      if (response.ok) {
        const data = await response.json()
        setScenarios(data.scenarios)
      }
    } catch (error) {
      console.error("Error loading scenarios:", error)
    }
  }

  const handleAnalyzeInTimeTravel = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedScenario) return

    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/time-travel/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_data: {
            model_id: formData.model_id,
            bias_characteristics: formData.bias_characteristics,
            performance_metrics: formData.performance_metrics
          },
          scenario_id: selectedScenario
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setAnalysis(result)
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeBiasEvolution = async () => {
    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/time-travel/bias-evolution", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_id: formData.model_id,
          bias_characteristics: formData.bias_characteristics,
          performance_metrics: formData.performance_metrics
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setBiasEvolution(result.bias_evolution)
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzePerformanceTimeline = async () => {
    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/time-travel/performance-timeline", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_id: formData.model_id,
          bias_characteristics: formData.bias_characteristics,
          performance_metrics: formData.performance_metrics
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setPerformanceComparisons(result.performance_comparisons)
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  // Load scenarios on component mount
  useState(() => {
    loadScenarios()
  })

  return (
    <div className="space-y-6">
      <Tabs defaultValue="scenarios" className="space-y-4">
        <TabsList>
          <TabsTrigger value="scenarios">Historical Scenarios</TabsTrigger>
          <TabsTrigger value="analysis">Time Travel Analysis</TabsTrigger>
          <TabsTrigger value="evolution">Bias Evolution</TabsTrigger>
          <TabsTrigger value="performance">Performance Timeline</TabsTrigger>
          <TabsTrigger value="dashboard">Time Travel Dashboard</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Historical Scenarios
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {scenarios.map((scenario) => (
                  <div key={scenario.scenario_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold">{scenario.name}</div>
                        <div className="text-sm text-gray-600">{scenario.description}</div>
                      </div>
                      <Badge className={timePeriodColors[scenario.time_period as keyof typeof timePeriodColors]}>
                        {scenario.time_period}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="font-medium text-gray-700">Historical Context</div>
                        <div className="text-gray-600">
                          {Object.entries(scenario.historical_context).map(([key, value]) => (
                            <div key={key}><span className="font-medium">{key}:</span> {value as string}</div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium text-gray-700">Bias Characteristics</div>
                        <div className="text-gray-600">
                          {Object.entries(scenario.bias_characteristics).map(([key, value]) => (
                            <div key={key}><span className="font-medium">{key}:</span> {(value as number * 100).toFixed(1)}%</div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Analyze Model in Historical Context
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAnalyzeInTimeTravel} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="model_id">Model ID</Label>
                    <Input
                      id="model_id"
                      value={formData.model_id}
                      onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                      placeholder="e.g., gpt-4-specialized"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="scenario">Historical Scenario</Label>
                    <Select value={selectedScenario} onValueChange={setSelectedScenario}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a historical scenario" />
                      </SelectTrigger>
                      <SelectContent>
                        {scenarios.map((scenario) => (
                          <SelectItem key={scenario.scenario_id} value={scenario.scenario_id}>
                            {scenario.name} ({scenario.time_period})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Bias Characteristics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="gender_bias">Gender Bias</Label>
                      <Input
                        id="gender_bias"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.bias_characteristics.gender_bias}
                        onChange={(e) => setFormData({
                          ...formData,
                          bias_characteristics: { ...formData.bias_characteristics, gender_bias: e.target.value }
                        })}
                        placeholder="0.15"
                      />
                    </div>
                    <div>
                      <Label htmlFor="racial_bias">Racial Bias</Label>
                      <Input
                        id="racial_bias"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.bias_characteristics.racial_bias}
                        onChange={(e) => setFormData({
                          ...formData,
                          bias_characteristics: { ...formData.bias_characteristics, racial_bias: e.target.value }
                        })}
                        placeholder="0.12"
                      />
                    </div>
                    <div>
                      <Label htmlFor="age_bias">Age Bias</Label>
                      <Input
                        id="age_bias"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.bias_characteristics.age_bias}
                        onChange={(e) => setFormData({
                          ...formData,
                          bias_characteristics: { ...formData.bias_characteristics, age_bias: e.target.value }
                        })}
                        placeholder="0.08"
                      />
                    </div>
                    <div>
                      <Label htmlFor="socioeconomic_bias">Socioeconomic Bias</Label>
                      <Input
                        id="socioeconomic_bias"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.bias_characteristics.socioeconomic_bias}
                        onChange={(e) => setFormData({
                          ...formData,
                          bias_characteristics: { ...formData.bias_characteristics, socioeconomic_bias: e.target.value }
                        })}
                        placeholder="0.10"
                      />
                    </div>
                  </div>
                </div>

                <Button type="submit" disabled={loading || !selectedScenario} className="w-full">
                  {loading ? "Analyzing..." : "Analyze in Historical Context"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {analysis && (
            <Card>
              <CardHeader>
                <CardTitle>Time Travel Analysis Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600">Historical Risk Level</div>
                    <Badge variant={analysis.risk_analysis.historical_risk_level === "HIGH" ? "destructive" : "secondary"}>
                      {analysis.risk_analysis.historical_risk_level}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Current Risk Level</div>
                    <Badge variant={analysis.risk_analysis.current_risk_level === "LOW" ? "default" : "secondary"}>
                      {analysis.risk_analysis.current_risk_level}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Risk Reduction</div>
                    <div className="text-lg font-bold text-green-600">
                      {(analysis.risk_analysis.risk_reduction * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
                  <div className="space-y-2">
                    {analysis.recommendations.map((rec, index) => (
                      <Alert key={index}>
                        <AlertDescription>{rec}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Ethical Assessment</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium text-gray-600">Historical Fairness</div>
                      <div className="text-lg font-bold text-red-600">
                        {(analysis.ethical_assessment.historical_fairness * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-600">Current Fairness</div>
                      <div className="text-lg font-bold text-green-600">
                        {(analysis.ethical_assessment.current_fairness * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="evolution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Bias Evolution Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button 
                  onClick={handleAnalyzeBiasEvolution}
                  disabled={loading || !formData.model_id}
                  className="w-full"
                >
                  {loading ? "Analyzing..." : "Analyze Bias Evolution"}
                </Button>

                {biasEvolution.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Bias Evolution Results</h3>
                    <div className="space-y-2">
                      {biasEvolution.map((evolution, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold">{evolution.bias_type}</div>
                              <div className="text-sm text-gray-600">
                                {evolution.historical_context} → {evolution.modern_context}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm">
                                Historical: {(evolution.historical_value * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm">
                                Current: {(evolution.current_value * 100).toFixed(1)}%
                              </div>
                              <Badge variant={evolution.change_direction === "decrease" ? "default" : "destructive"}>
                                {evolution.change_direction}
                              </Badge>
                            </div>
                          </div>
                          <div className="mt-2">
                            <div className="text-sm text-gray-600">Change Magnitude</div>
                            <Progress value={evolution.change_magnitude * 100} className="mt-1" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Timeline Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button 
                  onClick={handleAnalyzePerformanceTimeline}
                  disabled={loading || !formData.model_id}
                  className="w-full"
                >
                  {loading ? "Analyzing..." : "Analyze Performance Timeline"}
                </Button>

                {performanceComparisons.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Performance Timeline Results</h3>
                    <div className="space-y-2">
                      {performanceComparisons.map((comparison, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold">{comparison.metric}</div>
                              <div className="text-sm text-gray-600">{comparison.explanation}</div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm">
                                Historical: {(comparison.historical_performance * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm">
                                Current: {(comparison.current_performance * 100).toFixed(1)}%
                              </div>
                              <div className={`text-sm font-bold ${comparison.performance_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                Change: {(comparison.performance_change * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-4">
          <AITimeTravelDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function AITimeTravelDashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)

  const loadDashboard = async () => {
    try {
      const response = await fetch("http://localhost:8000/time-travel/dashboard")
      if (response.ok) {
        const data = await response.json()
        setDashboardData(data)
      }
    } catch (error) {
      console.error("Error loading dashboard:", error)
    }
  }

  // Load dashboard data on component mount
  useState(() => {
    loadDashboard()
  })

  if (!dashboardData) {
    return <div>Loading dashboard...</div>
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scenarios Analyzed</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_scenarios_analyzed}</div>
            <p className="text-xs text-muted-foreground">Historical scenarios analyzed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Models with History</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.models_with_historical_data}</div>
            <p className="text-xs text-muted-foreground">Models with historical data</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Bias Reduction</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(dashboardData.average_bias_reduction * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Average bias reduction</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance Improvement</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(dashboardData.average_performance_improvement * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Average performance improvement</p>
          </CardContent>
        </Card>
      </div>

      {/* Historical Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle>Historical Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.historical_scenarios.map((scenario: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{scenario.name}</div>
                    <div className="text-sm text-gray-600">Models analyzed: {scenario.models_analyzed}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold">{(scenario.avg_bias_score * 100).toFixed(1)}%</div>
                      <div className="text-xs text-gray-600">Avg Bias</div>
                    </div>
                    <Badge variant={scenario.risk_level === "HIGH" ? "destructive" : scenario.risk_level === "MEDIUM" ? "secondary" : "default"}>
                      {scenario.risk_level}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Analyses */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Time Travel Analyses</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.recent_analyses.map((analysis: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{analysis.model_id}</div>
                    <div className="text-sm text-gray-600">Scenario: {analysis.scenario}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {(analysis.bias_reduction * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Bias Reduction</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {(analysis.performance_improvement * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Performance</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 