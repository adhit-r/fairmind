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

interface ModelDNAProfile {
  model_id: string
  dna_signature: string
  parent_models: string[]
  child_models: string[]
  inheritance_type: string
  creation_date: string
  version: string
  algorithm_family: string
  bias_inheritance: any[]
  performance_characteristics: any
  ethical_framework: any
  risk_profile: any
}

interface BiasInheritancePattern {
  bias_type: string
  inheritance_type: string
  parent_value: number
  current_value: number
  change_magnitude: number
  change_direction: string
  explanation: string
}

interface ModelLineageNode {
  model_id: string
  generation: number
  parents: string[]
  children: string[]
  dna_signature: string
  creation_date: string
  bias_score: number
  performance_score: number
  risk_level: string
}

const inheritanceTypeColors = {
  amplified: "bg-red-100 text-red-800",
  reduced: "bg-green-100 text-green-800",
  inherited: "bg-blue-100 text-blue-800",
  new: "bg-yellow-100 text-yellow-800",
  eliminated: "bg-gray-100 text-gray-800"
}

export function AIDNAProfiler() {
  const [profile, setProfile] = useState<ModelDNAProfile | null>(null)
  const [lineage, setLineage] = useState<ModelLineageNode[]>([])
  const [evolution, setEvolution] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    model_id: "",
    parent_models: "",
    algorithm_family: "",
    version: "",
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

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch("http://localhost:8000/dna/profile", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_id: formData.model_id,
          parent_models: formData.parent_models.split(",").map(s => s.trim()).filter(s => s),
          algorithm_family: formData.algorithm_family,
          version: formData.version,
          bias_characteristics: formData.bias_characteristics,
          performance_metrics: formData.performance_metrics
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setProfile(result)
      } else {
        console.error("Profile creation failed")
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeLineage = async (modelId: string) => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/dna/lineage/${modelId}`)
      if (response.ok) {
        const result = await response.json()
        setLineage(result.lineage_tree)
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeEvolution = async (modelId: string) => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/dna/evolution/${modelId}`)
      if (response.ok) {
        const result = await response.json()
        setEvolution(result)
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile">DNA Profile</TabsTrigger>
          <TabsTrigger value="lineage">Lineage Analysis</TabsTrigger>
          <TabsTrigger value="evolution">Evolution Tracking</TabsTrigger>
          <TabsTrigger value="dashboard">DNA Dashboard</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Create AI Model DNA Profile
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateProfile} className="space-y-4">
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
                    <Label htmlFor="parent_models">Parent Models</Label>
                    <Input
                      id="parent_models"
                      value={formData.parent_models}
                      onChange={(e) => setFormData({ ...formData, parent_models: e.target.value })}
                      placeholder="e.g., gpt-4-base, bert-large"
                    />
                  </div>
                  <div>
                    <Label htmlFor="algorithm_family">Algorithm Family</Label>
                    <Input
                      id="algorithm_family"
                      value={formData.algorithm_family}
                      onChange={(e) => setFormData({ ...formData, algorithm_family: e.target.value })}
                      placeholder="e.g., Transformer, BERT, GPT"
                    />
                  </div>
                  <div>
                    <Label htmlFor="version">Version</Label>
                    <Input
                      id="version"
                      value={formData.version}
                      onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                      placeholder="e.g., 1.0.0"
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

                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? "Creating Profile..." : "Create DNA Profile"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {profile && (
            <Card>
              <CardHeader>
                <CardTitle>DNA Profile Created</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600">Model ID</div>
                    <div className="text-lg font-semibold">{profile.model_id}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">DNA Signature</div>
                    <div className="text-lg font-mono bg-gray-100 p-2 rounded">{profile.dna_signature}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Algorithm Family</div>
                    <div className="text-lg">{profile.algorithm_family}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600">Version</div>
                    <div className="text-lg">{profile.version}</div>
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-600">Parent Models</div>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {profile.parent_models.map((parent, index) => (
                      <Badge key={index} variant="outline">{parent}</Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="lineage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Lineage Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter model ID"
                    value={formData.model_id}
                    onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                  />
                  <Button 
                    onClick={() => handleAnalyzeLineage(formData.model_id)}
                    disabled={loading || !formData.model_id}
                  >
                    {loading ? "Analyzing..." : "Analyze Lineage"}
                  </Button>
                </div>

                {lineage.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Lineage Tree</h3>
                    <div className="space-y-2">
                      {lineage.map((node, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold">{node.model_id}</div>
                              <div className="text-sm text-gray-600">Generation {node.generation}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant={node.risk_level === "LOW" ? "default" : node.risk_level === "MEDIUM" ? "secondary" : "destructive"}>
                                {node.risk_level}
                              </Badge>
                              <div className="text-sm">
                                Bias: {(node.bias_score * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                          <div className="mt-2 text-xs text-gray-500">
                            DNA: {node.dna_signature}
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

        <TabsContent value="evolution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Evolution Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter model ID"
                    value={formData.model_id}
                    onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                  />
                  <Button 
                    onClick={() => handleAnalyzeEvolution(formData.model_id)}
                    disabled={loading || !formData.model_id}
                  >
                    {loading ? "Analyzing..." : "Track Evolution"}
                  </Button>
                </div>

                {evolution && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Evolution Path</h3>
                    <div className="space-y-2">
                      {evolution.evolution_path.map((node: any, index: number) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold">{node.model_id}</div>
                              <div className="text-sm text-gray-600">Generation {node.generation}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="text-sm">
                                Performance: {(node.performance_score * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm">
                                Bias: {(node.bias_score * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {evolution.bias_evolution.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mt-4">Bias Evolution</h3>
                        <div className="space-y-2">
                          {evolution.bias_evolution.map((pattern: BiasInheritancePattern, index: number) => (
                            <div key={index} className="border rounded-lg p-3">
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="font-medium">{pattern.bias_type}</div>
                                  <div className="text-sm text-gray-600">{pattern.explanation}</div>
                                </div>
                                <Badge className={inheritanceTypeColors[pattern.inheritance_type as keyof typeof inheritanceTypeColors]}>
                                  {pattern.inheritance_type}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-4">
          <AIDNADashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function AIDNADashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)

  const loadDashboard = async () => {
    try {
      const response = await fetch("http://localhost:8000/dna/dashboard")
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
            <CardTitle className="text-sm font-medium">Models Profiled</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.total_models_profiled}</div>
            <p className="text-xs text-muted-foreground">Total models with DNA profiles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">With Lineage</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.models_with_lineage}</div>
            <p className="text-xs text-muted-foreground">Models with known lineage</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Generations</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.average_generations}</div>
            <p className="text-xs text-muted-foreground">Average generations per family</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bias Changes</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{String(Object.values(dashboardData.bias_inheritance_stats).reduce((a: any, b: any) => (a || 0) + (b || 0), 0))}</div>
            <p className="text-xs text-muted-foreground">Total bias inheritance events</p>
          </CardContent>
        </Card>
      </div>

      {/* Lineage Families */}
      <Card>
        <CardHeader>
          <CardTitle>Lineage Families</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {dashboardData.lineage_families.map((family: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">{family.family_name}</div>
                    <div className="text-sm text-gray-600">Root: {family.root_model}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold">{family.total_models}</div>
                      <div className="text-xs text-gray-600">Models</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold">{family.generations}</div>
                      <div className="text-xs text-gray-600">Generations</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold">{(family.avg_bias_score * 100).toFixed(1)}%</div>
                      <div className="text-xs text-gray-600">Avg Bias</div>
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