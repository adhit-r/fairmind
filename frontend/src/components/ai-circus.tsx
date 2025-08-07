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

interface TestScenario {
  scenario_id: string
  name: string
  description: string
  category: string
  difficulty: string
  expected_outcome: string
  success_criteria: Record<string, any>
}

interface StressTest {
  test_id: string
  name: string
  description: string
  test_type: string
  parameters: Record<string, any>
  results: Record<string, any>
  passed: boolean
  duration: number
}

interface EdgeCase {
  case_id: string
  name: string
  description: string
  input_data: any
  expected_behavior: string
  actual_behavior: string
  severity: string
  category: string
}

interface AdversarialChallenge {
  challenge_id: string
  name: string
  description: string
  attack_type: string
  success_rate: number
  robustness_score: number
  vulnerabilities_found: string[]
}

interface TestResults {
  model_id: string
  test_timestamp: string
  scenarios: any[]
  stress_tests: any[]
  edge_cases: any[]
  adversarial_challenges: any[]
  overall_score: number
  recommendations: string[]
}

const difficultyColors = {
  "low": "bg-green-100 text-green-800",
  "medium": "bg-yellow-100 text-yellow-800",
  "high": "bg-red-100 text-red-800"
}

const categoryColors = {
  "bias": "bg-purple-100 text-purple-800",
  "security": "bg-red-100 text-red-800",
  "reliability": "bg-blue-100 text-blue-800",
  "performance": "bg-green-100 text-green-800",
  "ethics": "bg-orange-100 text-orange-800"
}

export function AICircus() {
  const [scenarios, setScenarios] = useState<TestScenario[]>([])
  const [stressTests, setStressTests] = useState<StressTest[]>([])
  const [edgeCases, setEdgeCases] = useState<EdgeCase[]>([])
  const [adversarialChallenges, setAdversarialChallenges] = useState<AdversarialChallenge[]>([])
  const [testResults, setTestResults] = useState<TestResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedScenario, setSelectedScenario] = useState<string>("")
  const [formData, setFormData] = useState({
    model_id: "",
    test_type: "comprehensive"
  })

  const loadScenarios = async () => {
    try {
      const response = await fetch("http://localhost:8000/circus/scenarios")
      if (response.ok) {
        const data = await response.json()
        setScenarios(data.scenarios)
      }
    } catch (error) {
      console.error("Error loading scenarios:", error)
    }
  }

  const runComprehensiveTest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.model_id) return

    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/circus/run-test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_id: formData.model_id,
          scenario_id: selectedScenario || "comprehensive"
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setTestResults(result)
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
          <TabsTrigger value="scenarios">Test Scenarios</TabsTrigger>
          <TabsTrigger value="stress-tests">Stress Tests</TabsTrigger>
          <TabsTrigger value="edge-cases">Edge Cases</TabsTrigger>
          <TabsTrigger value="adversarial">Adversarial Challenges</TabsTrigger>
          <TabsTrigger value="run-test">Run Test</TabsTrigger>
          <TabsTrigger value="dashboard">Circus Dashboard</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Test Scenarios
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
                      <div className="flex gap-2">
                        <Badge className={categoryColors[scenario.category as keyof typeof categoryColors]}>
                          {scenario.category}
                        </Badge>
                        <Badge className={difficultyColors[scenario.difficulty as keyof typeof difficultyColors]}>
                          {scenario.difficulty}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Expected Outcome:</span> {scenario.expected_outcome}</div>
                      <div><span className="font-medium">Success Criteria:</span></div>
                      <div className="ml-4 text-gray-600">
                        {Object.entries(scenario.success_criteria).map(([key, value]) => (
                          <div key={key}><span className="font-medium">{key}:</span> {value as string}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stress-tests" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Stress Tests
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stressTests.map((test) => (
                  <div key={test.test_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold">{test.name}</div>
                        <div className="text-sm text-gray-600">{test.description}</div>
                      </div>
                      <Badge variant={test.passed ? "default" : "destructive"}>
                        {test.passed ? "PASSED" : "FAILED"}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="font-medium text-gray-700">Parameters</div>
                        <div className="text-gray-600">
                          {Object.entries(test.parameters).map(([key, value]) => (
                            <div key={key}><span className="font-medium">{key}:</span> {value as string}</div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium text-gray-700">Results</div>
                        <div className="text-gray-600">
                          {Object.entries(test.results).map(([key, value]) => (
                            <div key={key}><span className="font-medium">{key}:</span> {value as string}</div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      Duration: {test.duration.toFixed(1)}s
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="edge-cases" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                Edge Cases
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {edgeCases.map((case_) => (
                  <div key={case_.case_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold">{case_.name}</div>
                        <div className="text-sm text-gray-600">{case_.description}</div>
                      </div>
                      <Badge variant={case_.severity === "high" ? "destructive" : case_.severity === "medium" ? "secondary" : "default"}>
                        {case_.severity}
                      </Badge>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Expected:</span> {case_.expected_behavior}</div>
                      <div><span className="font-medium">Actual:</span> {case_.actual_behavior}</div>
                      <div><span className="font-medium">Category:</span> {case_.category}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="adversarial" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                Adversarial Challenges
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {adversarialChallenges.map((challenge) => (
                  <div key={challenge.challenge_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold">{challenge.name}</div>
                        <div className="text-sm text-gray-600">{challenge.description}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm">
                          Success Rate: {(challenge.success_rate * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm">
                          Robustness: {(challenge.robustness_score * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Attack Type:</span> {challenge.attack_type}</div>
                      <div><span className="font-medium">Vulnerabilities:</span></div>
                      <div className="ml-4 text-gray-600">
                        {challenge.vulnerabilities_found.map((vuln, index) => (
                          <div key={index}>• {vuln}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="run-test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Run Comprehensive Test
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={runComprehensiveTest} className="space-y-4">
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
                    <Label htmlFor="test_type">Test Type</Label>
                    <Select value={formData.test_type} onValueChange={(value) => setFormData({ ...formData, test_type: value })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select test type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="comprehensive">Comprehensive</SelectItem>
                        <SelectItem value="stress">Stress Test</SelectItem>
                        <SelectItem value="edge-case">Edge Case</SelectItem>
                        <SelectItem value="adversarial">Adversarial</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button type="submit" disabled={loading || !formData.model_id} className="w-full">
                  {loading ? "Running Tests..." : "Run Comprehensive Test"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {testResults && (
            <Card>
              <CardHeader>
                <CardTitle>Test Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600">Overall Score</div>
                    <div className="text-2xl font-bold text-green-600">
                      {(testResults.overall_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Scenarios Tested</div>
                    <div className="text-2xl font-bold">{testResults.scenarios.length}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Tests Passed</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {testResults.scenarios.filter(s => s.passed).length}/{testResults.scenarios.length}
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
                  <div className="space-y-2">
                    {testResults.recommendations.map((rec, index) => (
                      <Alert key={index}>
                        <AlertDescription>{rec}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Test Details</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="font-medium">Scenarios</div>
                      <div className="space-y-2">
                        {testResults.scenarios.map((scenario, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span>{scenario.name}</span>
                            <Badge variant={scenario.passed ? "default" : "destructive"}>
                              {scenario.passed ? "PASS" : "FAIL"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="font-medium">Stress Tests</div>
                      <div className="space-y-2">
                        {testResults.stress_tests.map((test, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span>{test.name}</span>
                            <Badge variant={test.passed ? "default" : "destructive"}>
                              {test.passed ? "PASS" : "FAIL"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="font-medium">Edge Cases</div>
                      <div className="space-y-2">
                        {testResults.edge_cases.map((case_, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span>{case_.name}</span>
                            <Badge variant={case_.passed ? "default" : "destructive"}>
                              {case_.passed ? "PASS" : "FAIL"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="font-medium">Adversarial Challenges</div>
                      <div className="space-y-2">
                        {testResults.adversarial_challenges.map((challenge, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span>{challenge.name}</span>
                            <div className="text-sm">
                              Robustness: {(challenge.robustness_score * 100).toFixed(1)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-4">
          <AICircusDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function AICircusDashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)

  const loadDashboard = async () => {
    try {
      const response = await fetch("http://localhost:8000/circus/dashboard")
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
            <CardTitle className="text-sm font-medium">Total Tests Run</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_tests_run}</div>
            <p className="text-xs text-muted-foreground">Tests executed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Models Tested</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.models_tested}</div>
            <p className="text-xs text-muted-foreground">Models tested</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(dashboardData.average_score * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Average test score</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{dashboardData.critical_issues}</div>
            <p className="text-xs text-muted-foreground">Critical issues found</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tests */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Tests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.recent_tests.map((test: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{test.model_id}</div>
                    <div className="text-sm text-gray-600">Type: {test.test_type}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {(test.score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {test.duration_minutes}m
                      </div>
                      <div className="text-xs text-gray-600">Duration</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-red-600">
                        {test.issues_found}
                      </div>
                      <div className="text-xs text-gray-600">Issues</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Test Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Test Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.test_categories.map((category: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold capitalize">{category.category}</div>
                    <div className="text-sm text-gray-600">Tests run: {category.tests_run}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold">{(category.avg_score * 100).toFixed(1)}%</div>
                      <div className="text-xs text-gray-600">Avg Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {(category.pass_rate * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Pass Rate</div>
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