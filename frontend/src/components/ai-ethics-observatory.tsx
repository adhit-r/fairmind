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

interface EthicsFramework {
  framework_id: string
  name: string
  description: string
  principles: string[]
  region: string
}

interface EthicsScore {
  model_id: string
  framework_id: string
  overall_score: number
  compliance_status: string
  recommendations: string[]
}

const complianceColors = {
  "compliant": "bg-green-100 text-green-800",
  "partially_compliant": "bg-yellow-100 text-yellow-800",
  "non_compliant": "bg-red-100 text-red-800"
}

export function AIEthicsObservatory() {
  const [frameworks, setFrameworks] = useState<EthicsFramework[]>([])
  const [selectedFramework, setSelectedFramework] = useState<string>("")
  const [ethicsScore, setEthicsScore] = useState<EthicsScore | null>(null)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    model_id: "",
    model_characteristics: {
      bias_level: "",
      transparency_level: "",
      safety_level: "",
      privacy_level: ""
    }
  })

  const loadFrameworks = async () => {
    try {
      const response = await fetch("http://localhost:8000/ethics/frameworks")
      if (response.ok) {
        const data = await response.json()
        setFrameworks(data.frameworks)
      }
    } catch (error) {
      console.error("Error loading frameworks:", error)
    }
  }

  const handleAssessEthics = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFramework) return

    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/ethics/assess", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_data: {
            model_id: formData.model_id,
            characteristics: formData.model_characteristics
          },
          framework_id: selectedFramework
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setEthicsScore(result)
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  // Load frameworks on component mount
  useState(() => {
    loadFrameworks()
  })

  return (
    <div className="space-y-6">
      <Tabs defaultValue="frameworks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="frameworks">Ethics Frameworks</TabsTrigger>
          <TabsTrigger value="assessment">Ethics Assessment</TabsTrigger>
          <TabsTrigger value="dashboard">Global Observatory</TabsTrigger>
        </TabsList>

        <TabsContent value="frameworks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Global Ethics Frameworks
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {frameworks.map((framework) => (
                  <div key={framework.framework_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold">{framework.name}</div>
                        <div className="text-sm text-gray-600">{framework.description}</div>
                      </div>
                      <Badge variant="outline">{framework.region}</Badge>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="font-medium text-gray-700">Principles:</div>
                      <div className="flex flex-wrap gap-2">
                        {framework.principles.map((principle, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {principle}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assessment" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Ethics Assessment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAssessEthics} className="space-y-4">
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
                    <Label htmlFor="framework">Ethics Framework</Label>
                    <Select value={selectedFramework} onValueChange={setSelectedFramework}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an ethics framework" />
                      </SelectTrigger>
                      <SelectContent>
                        {frameworks.map((framework) => (
                          <SelectItem key={framework.framework_id} value={framework.framework_id}>
                            {framework.name} ({framework.region})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Model Characteristics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="bias_level">Bias Level (0-1)</Label>
                      <Input
                        id="bias_level"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.model_characteristics.bias_level}
                        onChange={(e) => setFormData({
                          ...formData,
                          model_characteristics: { ...formData.model_characteristics, bias_level: e.target.value }
                        })}
                        placeholder="0.15"
                      />
                    </div>
                    <div>
                      <Label htmlFor="transparency_level">Transparency Level (0-1)</Label>
                      <Input
                        id="transparency_level"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.model_characteristics.transparency_level}
                        onChange={(e) => setFormData({
                          ...formData,
                          model_characteristics: { ...formData.model_characteristics, transparency_level: e.target.value }
                        })}
                        placeholder="0.8"
                      />
                    </div>
                    <div>
                      <Label htmlFor="safety_level">Safety Level (0-1)</Label>
                      <Input
                        id="safety_level"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.model_characteristics.safety_level}
                        onChange={(e) => setFormData({
                          ...formData,
                          model_characteristics: { ...formData.model_characteristics, safety_level: e.target.value }
                        })}
                        placeholder="0.9"
                      />
                    </div>
                    <div>
                      <Label htmlFor="privacy_level">Privacy Level (0-1)</Label>
                      <Input
                        id="privacy_level"
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={formData.model_characteristics.privacy_level}
                        onChange={(e) => setFormData({
                          ...formData,
                          model_characteristics: { ...formData.model_characteristics, privacy_level: e.target.value }
                        })}
                        placeholder="0.85"
                      />
                    </div>
                  </div>
                </div>

                <Button type="submit" disabled={loading || !selectedFramework} className="w-full">
                  {loading ? "Assessing..." : "Assess Ethics Compliance"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {ethicsScore && (
            <Card>
              <CardHeader>
                <CardTitle>Ethics Assessment Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600">Overall Score</div>
                    <div className="text-2xl font-bold text-green-600">
                      {(ethicsScore.overall_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Compliance Status</div>
                    <Badge className={complianceColors[ethicsScore.compliance_status as keyof typeof complianceColors]}>
                      {ethicsScore.compliance_status.toUpperCase()}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Framework</div>
                    <div className="text-lg font-semibold">{ethicsScore.framework_id}</div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
                  <div className="space-y-2">
                    {ethicsScore.recommendations.map((rec, index) => (
                      <Alert key={index}>
                        <AlertDescription>{rec}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-4">
          <AIEthicsDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function AIEthicsDashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)

  const loadDashboard = async () => {
    try {
      const response = await fetch("http://localhost:8000/ethics/dashboard")
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
            <CardTitle className="text-sm font-medium">Total Frameworks</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_frameworks}</div>
            <p className="text-xs text-muted-foreground">Global frameworks</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Models Assessed</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_models_assessed}</div>
            <p className="text-xs text-muted-foreground">Models evaluated</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Global Compliance</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(dashboardData.global_compliance_rate * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Average compliance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Violations</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{dashboardData.critical_violations}</div>
            <p className="text-xs text-muted-foreground">Critical violations</p>
          </CardContent>
        </Card>
      </div>

      {/* Frameworks */}
      <Card>
        <CardHeader>
          <CardTitle>Ethics Frameworks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.frameworks.map((framework: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{framework.name}</div>
                    <div className="text-sm text-gray-600">Framework ID: {framework.framework_id}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-green-600">
                      {(framework.compliance_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-600">Compliance Rate</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Violations */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Violations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.recent_violations.map((violation: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{violation.model_id}</div>
                    <div className="text-sm text-gray-600">Framework: {violation.framework}</div>
                  </div>
                  <Badge variant={violation.severity === "critical" ? "destructive" : "secondary"}>
                    {violation.severity.toUpperCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 