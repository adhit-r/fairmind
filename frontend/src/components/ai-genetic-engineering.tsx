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
import { Checkbox } from "@/components/ui/checkbox"

interface ModelAnalysis {
  model_id: string
  current_bias_score: number
  safety_score: number
  safety_level: string
  recommendations: any[]
  available_tools: any[]
  available_enhancements: any[]
}

interface ModelModification {
  modification_id: string
  model_id: string
  modification_type: string
  target_biases: string[]
  removal_methods: string[]
  safety_level: string
  performance_impact: any
  bias_reduction: any
  ethical_improvements: any
  validation_results: any
  created_at: string
}

interface GeneticEngineeringSession {
  session_id: string
  model_id: string
  modifications: ModelModification[]
  overall_impact: any
  safety_score: number
  fairness_score: number
  performance_score: number
  created_at: string
}

const safetyLevelColors = {
  low: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-green-100 text-green-800",
  critical: "bg-red-100 text-red-800"
}

export function AIGeneticEngineering() {
  const [analysis, setAnalysis] = useState<ModelAnalysis | null>(null)
  const [session, setSession] = useState<GeneticEngineeringSession | null>(null)
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
  const [selectedTools, setSelectedTools] = useState<string[]>([])
  const [selectedEnhancements, setSelectedEnhancements] = useState<string[]>([])

  const handleAnalyzeModel = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch("http://localhost:8000/genetic-engineering/analyze", {
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
        setAnalysis(result)
      } else {
        console.error("Model analysis failed")
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleApplyModification = async () => {
    if (!analysis || selectedTools.length === 0) return

    setLoading(true)
    try {
      const modification_config = {
        target_biases: Object.keys(formData.bias_characteristics).filter(key => 
          formData.bias_characteristics[key as keyof typeof formData.bias_characteristics] !== ""
        ),
        removal_methods: selectedTools,
        enhancement_methods: selectedEnhancements,
        reduction_factor: 0.5,
        safety_level: "medium"
      }

      const response = await fetch("http://localhost:8000/genetic-engineering/apply-modification", {
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
          modification_config
        }),
      })

      if (response.ok) {
        const result = await response.json()
        console.log("Modification applied:", result)
        
        // Create session with the modification
        const sessionResponse = await fetch("http://localhost:8000/genetic-engineering/session", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model_id: formData.model_id,
            modifications: [result.modification]
          }),
        })

        if (sessionResponse.ok) {
          const sessionResult = await sessionResponse.json()
          setSession(sessionResult)
        }
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleToolSelection = (toolId: string, checked: boolean) => {
    if (checked) {
      setSelectedTools([...selectedTools, toolId])
    } else {
      setSelectedTools(selectedTools.filter(id => id !== toolId))
    }
  }

  const handleEnhancementSelection = (enhancementId: string, checked: boolean) => {
    if (checked) {
      setSelectedEnhancements([...selectedEnhancements, enhancementId])
    } else {
      setSelectedEnhancements(selectedEnhancements.filter(id => id !== enhancementId))
    }
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="analyze" className="space-y-4">
        <TabsList>
          <TabsTrigger value="analyze">Model Analysis</TabsTrigger>
          <TabsTrigger value="tools">Genetic Tools</TabsTrigger>
          <TabsTrigger value="session">Engineering Session</TabsTrigger>
          <TabsTrigger value="dashboard">Engineering Dashboard</TabsTrigger>
        </TabsList>

        <TabsContent value="analyze" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Analyze Model for Genetic Engineering
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAnalyzeModel} className="space-y-4">
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
                        placeholder="0.25"
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
                        placeholder="0.18"
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
                        placeholder="0.12"
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
                        placeholder="0.15"
                      />
                    </div>
                  </div>
                </div>

                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? "Analyzing..." : "Analyze Model"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {analysis && (
            <Card>
              <CardHeader>
                <CardTitle>Analysis Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600">Current Bias Score</div>
                    <div className="text-2xl font-bold text-red-600">
                      {(analysis.current_bias_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Safety Score</div>
                    <div className="text-2xl font-bold text-green-600">
                      {(analysis.safety_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Safety Level</div>
                    <Badge className={safetyLevelColors[analysis.safety_level as keyof typeof safetyLevelColors]}>
                      {analysis.safety_level.toUpperCase()}
                    </Badge>
                  </div>
                </div>

                {analysis.recommendations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
                    <div className="space-y-2">
                      {analysis.recommendations.map((rec, index) => (
                        <Alert key={index}>
                          <AlertDescription>
                            <div className="font-medium">{rec.type.replace("_", " ").toUpperCase()}</div>
                            <div className="text-sm text-gray-600">
                              Priority: {rec.priority} | Expected Improvement: {(rec.expected_improvement * 100).toFixed(1)}%
                            </div>
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button 
                    onClick={handleApplyModification}
                    disabled={loading || selectedTools.length === 0}
                    className="flex-1"
                  >
                    {loading ? "Applying..." : "Apply Genetic Engineering"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Available Genetic Engineering Tools</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Bias Removal Tools</h3>
                  <div className="space-y-3">
                    {analysis?.available_tools.map((tool: any) => (
                      <div key={tool.tool_id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-semibold">{tool.name}</div>
                            <div className="text-sm text-gray-600 mt-1">{tool.description}</div>
                            <div className="flex items-center gap-4 mt-2">
                              <div className="text-sm">
                                <span className="font-medium">Effectiveness:</span> {(tool.effectiveness_score * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm">
                                <span className="font-medium">Safety:</span> {(tool.safety_score * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm">
                                <span className="font-medium">Performance Impact:</span> {(tool.performance_impact * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                          <div className="ml-4">
                            <Checkbox
                              checked={selectedTools.includes(tool.tool_id)}
                              onCheckedChange={(checked) => handleToolSelection(tool.tool_id, checked as boolean)}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4">Fairness Enhancements</h3>
                  <div className="space-y-3">
                    {analysis?.available_enhancements.map((enhancement: any) => (
                      <div key={enhancement.enhancement_id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-semibold">{enhancement.name}</div>
                            <div className="text-sm text-gray-600 mt-1">{enhancement.description}</div>
                            <div className="flex items-center gap-4 mt-2">
                              <div className="text-sm">
                                <span className="font-medium">Expected Improvement:</span> {(enhancement.expected_improvement * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm">
                                <span className="font-medium">Method:</span> {enhancement.implementation_method}
                              </div>
                            </div>
                          </div>
                          <div className="ml-4">
                            <Checkbox
                              checked={selectedEnhancements.includes(enhancement.enhancement_id)}
                              onCheckedChange={(checked) => handleEnhancementSelection(enhancement.enhancement_id, checked as boolean)}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="session" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Genetic Engineering Session</CardTitle>
            </CardHeader>
            <CardContent>
              {session ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm font-medium text-gray-600">Safety Score</div>
                      <div className="text-2xl font-bold text-green-600">
                        {(session.safety_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-600">Fairness Score</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {(session.fairness_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-600">Performance Score</div>
                      <div className="text-2xl font-bold text-purple-600">
                        {(session.performance_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-2">Modifications Applied</h3>
                    <div className="space-y-2">
                      {session.modifications.map((mod, index) => (
                        <div key={index} className="border rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-medium">{mod.modification_type.replace("_", " ").toUpperCase()}</div>
                              <div className="text-sm text-gray-600">
                                Target Biases: {mod.target_biases.join(", ")}
                              </div>
                            </div>
                            <Badge variant="outline">
                              {mod.safety_level.toUpperCase()}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-2">Overall Impact</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm font-medium text-gray-600">Total Bias Reduction</div>
                        <div className="text-lg font-bold text-green-600">
                          {(session.overall_impact.total_bias_reduction * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-600">Performance Impact</div>
                        <div className="text-lg font-bold text-red-600">
                          {(session.overall_impact.total_performance_impact * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500">
                  No active genetic engineering session. Analyze a model and apply modifications to create a session.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-4">
          <AIGeneticEngineeringDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function AIGeneticEngineeringDashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)

  const loadDashboard = async () => {
    try {
      const response = await fetch("http://localhost:8000/genetic-engineering/dashboard")
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
            <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_sessions}</div>
            <p className="text-xs text-muted-foreground">Genetic engineering sessions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful Modifications</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.successful_modifications}</div>
            <p className="text-xs text-muted-foreground">Successful modifications</p>
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
            <CardTitle className="text-sm font-medium">Safety Score</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(dashboardData.safety_score * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Overall safety score</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.recent_sessions.map((session: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{session.model_id}</div>
                    <div className="text-sm text-gray-600">Session: {session.session_id}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold">{session.modifications_applied}</div>
                      <div className="text-xs text-gray-600">Modifications</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {(session.bias_reduction * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Bias Reduction</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-red-600">
                        {(session.performance_impact * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Performance Impact</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Popular Tools */}
      <Card>
        <CardHeader>
          <CardTitle>Popular Tools</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.popular_tools.map((tool: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{tool.tool_name}</div>
                    <div className="text-sm text-gray-600">
                      Usage: {tool.usage_count} times | Success Rate: {(tool.success_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold">{(tool.avg_effectiveness * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-600">Avg Effectiveness</div>
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