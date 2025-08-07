"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"

interface GeographicBiasAnalysis {
  model_id: string
  source_country: string
  target_country: string
  bias_detected: boolean
  bias_score: number
  performance_drop: number
  affected_metrics: string[]
  risk_level: string
  recommendations: string[]
  cultural_factors: Record<string, string>
  compliance_issues: string[]
}

const countries = [
  "USA", "UK", "Germany", "France", "Japan", "India", "Brazil", "Australia",
  "Canada", "China", "South Korea", "Mexico", "Italy", "Spain", "Netherlands",
  "Sweden", "Norway", "Denmark", "Finland", "Switzerland", "Austria"
]

const riskLevelColors = {
  LOW: "bg-green-100 text-green-800",
  MEDIUM: "bg-yellow-100 text-yellow-800",
  HIGH: "bg-orange-100 text-orange-800",
  CRITICAL: "bg-red-100 text-red-800"
}

export function GeographicBiasDetector() {
  const [analysis, setAnalysis] = useState<GeographicBiasAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    model_id: "",
    source_country: "",
    target_country: "",
    source_accuracy: "",
    target_accuracy: "",
    cultural_factors: {
      language: "",
      economic: "",
      cultural: "",
      regulatory: ""
    }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch("http://localhost:8000/analyze/geographic-bias", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_id: formData.model_id,
          source_country: formData.source_country,
          target_country: formData.target_country,
          model_performance_data: {
            [formData.source_country]: {
              accuracy: parseFloat(formData.source_accuracy) || 0.85
            },
            [formData.target_country]: {
              accuracy: parseFloat(formData.target_accuracy) || 0.75
            }
          },
          demographic_data: {},
          cultural_factors: formData.cultural_factors
        }),
      })

      if (response.ok) {
        const result = await response.json()
        setAnalysis(result)
      } else {
        console.error("Analysis failed")
      }
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Geographic Bias Detection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="model_id">Model ID</Label>
                <Input
                  id="model_id"
                  value={formData.model_id}
                  onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                  placeholder="e.g., credit-scoring-v1"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="source_country">Source Country</Label>
                <Select
                  value={formData.source_country}
                  onValueChange={(value) => setFormData({ ...formData, source_country: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select source country" />
                  </SelectTrigger>
                  <SelectContent>
                    {countries.map((country) => (
                      <SelectItem key={country} value={country}>
                        {country}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="target_country">Target Country</Label>
                <Select
                  value={formData.target_country}
                  onValueChange={(value) => setFormData({ ...formData, target_country: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select target country" />
                  </SelectTrigger>
                  <SelectContent>
                    {countries.map((country) => (
                      <SelectItem key={country} value={country}>
                        {country}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="source_accuracy">Source Country Accuracy</Label>
                <Input
                  id="source_accuracy"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={formData.source_accuracy}
                  onChange={(e) => setFormData({ ...formData, source_accuracy: e.target.value })}
                  placeholder="0.85"
                />
              </div>

              <div>
                <Label htmlFor="target_accuracy">Target Country Accuracy</Label>
                <Input
                  id="target_accuracy"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={formData.target_accuracy}
                  onChange={(e) => setFormData({ ...formData, target_accuracy: e.target.value })}
                  placeholder="0.75"
                />
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Cultural Factors</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="language">Language Differences</Label>
                  <Input
                    id="language"
                    value={formData.cultural_factors.language}
                    onChange={(e) => setFormData({
                      ...formData,
                      cultural_factors: { ...formData.cultural_factors, language: e.target.value }
                    })}
                    placeholder="e.g., English vs Hindi"
                  />
                </div>
                <div>
                  <Label htmlFor="economic">Economic Factors</Label>
                  <Input
                    id="economic"
                    value={formData.cultural_factors.economic}
                    onChange={(e) => setFormData({
                      ...formData,
                      cultural_factors: { ...formData.cultural_factors, economic: e.target.value }
                    })}
                    placeholder="e.g., GDP per capita differences"
                  />
                </div>
                <div>
                  <Label htmlFor="cultural">Cultural Norms</Label>
                  <Input
                    id="cultural"
                    value={formData.cultural_factors.cultural}
                    onChange={(e) => setFormData({
                      ...formData,
                      cultural_factors: { ...formData.cultural_factors, cultural: e.target.value }
                    })}
                    placeholder="e.g., Social customs, traditions"
                  />
                </div>
                <div>
                  <Label htmlFor="regulatory">Regulatory Environment</Label>
                  <Input
                    id="regulatory"
                    value={formData.cultural_factors.regulatory}
                    onChange={(e) => setFormData({
                      ...formData,
                      cultural_factors: { ...formData.cultural_factors, regulatory: e.target.value }
                    })}
                    placeholder="e.g., Data protection laws"
                  />
                </div>
              </div>
            </div>

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Analyzing..." : "Analyze Geographic Bias"}
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
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {analysis.bias_score.toFixed(3)}
                </div>
                <div className="text-sm text-gray-600">Bias Score</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {analysis.performance_drop.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Performance Drop</div>
              </div>
              <div className="text-center">
                <Badge className={riskLevelColors[analysis.risk_level as keyof typeof riskLevelColors]}>
                  {analysis.risk_level}
                </Badge>
                <div className="text-sm text-gray-600 mt-1">Risk Level</div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Bias Detection</h4>
              <Alert className={analysis.bias_detected ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"}>
                <AlertDescription>
                  {analysis.bias_detected 
                    ? "⚠️ Geographic bias detected. Model performance varies significantly between countries."
                    : "✅ No significant geographic bias detected."
                  }
                </AlertDescription>
              </Alert>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Affected Metrics</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.affected_metrics.map((metric) => (
                  <Badge key={metric} variant="outline">
                    {metric}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Recommendations</h4>
              <ul className="space-y-1">
                {analysis.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {analysis.compliance_issues.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 text-red-600">Compliance Issues</h4>
                <ul className="space-y-1">
                  {analysis.compliance_issues.map((issue, index) => (
                    <li key={index} className="flex items-start gap-2 text-red-600">
                      <span className="mt-1">⚠️</span>
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h4 className="font-semibold mb-2">Cultural Factors Analysis</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(analysis.cultural_factors).map(([factor, value]) => (
                  <div key={factor}>
                    <div className="text-sm font-medium text-gray-600 capitalize">
                      {factor.replace('_', ' ')}
                    </div>
                    <div className="text-sm">{value || "Not specified"}</div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 