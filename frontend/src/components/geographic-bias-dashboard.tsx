"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Globe, MapPin, Users2, TrendingUp, TrendingDown, AlertTriangle, Activity, BarChart3, Target, Network } from "lucide-react"
import { BiasDetectionRadar } from "@/components/charts/bias-detection-radar"
import { DistributionChart } from "@/components/charts/distribution-chart"

const geographicMetrics = [
  { label: "COUNTRIES ANALYZED", value: "23", trend: "+3", icon: Globe },
  { label: "HIGH RISK COUNTRIES", value: "4", trend: "-1", icon: AlertTriangle },
  { label: "CULTURAL FACTORS", value: "12", trend: "+2", icon: Users2 },
  { label: "CROSS-COUNTRY TESTS", value: "156", trend: "+18", icon: Network },
]

const countryAnalyses = [
  { source: "USA", target: "India", model: "LOAN MODEL V1", bias_score: 0.15, risk_level: "LOW", performance_drop: 2.3, cultural_factors: ["LANGUAGE", "ECONOMIC"] },
  { source: "USA", target: "Nigeria", model: "GPT4 HIRING ASSISTANT", bias_score: 0.32, risk_level: "HIGH", performance_drop: 15.7, cultural_factors: ["EDUCATION", "GENDER"] },
  { source: "UK", target: "Kenya", model: "CREDIT SCORING V3", bias_score: 0.28, risk_level: "MEDIUM", performance_drop: 8.9, cultural_factors: ["ECONOMIC", "REGIONAL"] },
  { source: "Germany", target: "Brazil", model: "CLAUDE LEGAL ADVISOR", bias_score: 0.08, risk_level: "LOW", performance_drop: 1.2, cultural_factors: ["LANGUAGE"] },
  { source: "Japan", target: "Mexico", model: "FRAUD DETECTION V2", bias_score: 0.45, risk_level: "HIGH", performance_drop: 12.4, cultural_factors: ["CULTURAL", "REGULATORY"] },
]

const culturalFactors = [
  { factor: "LANGUAGE DIFFERENCES", weight: 0.3, impact: "HIGH", affected_countries: ["India", "Nigeria", "Brazil"], bias_contribution: 0.25 },
  { factor: "ECONOMIC FACTORS", weight: 0.25, impact: "MEDIUM", affected_countries: ["Kenya", "Nigeria"], bias_contribution: 0.18 },
  { factor: "CULTURAL NORMS", weight: 0.25, impact: "HIGH", affected_countries: ["India", "Brazil"], bias_contribution: 0.22 },
  { factor: "REGULATORY ENVIRONMENT", weight: 0.2, impact: "MEDIUM", affected_countries: ["Brazil", "India"], bias_contribution: 0.15 },
]

const regionalBiasPatterns = [
  { region: "NORTH AMERICA", bias_score: 0.12, models_affected: 8, risk_level: "LOW" },
  { region: "EUROPE", bias_score: 0.18, models_affected: 12, risk_level: "MEDIUM" },
  { region: "ASIA PACIFIC", bias_score: 0.28, models_affected: 15, risk_level: "HIGH" },
  { region: "AFRICA", bias_score: 0.35, models_affected: 6, risk_level: "HIGH" },
  { region: "LATIN AMERICA", bias_score: 0.22, models_affected: 9, risk_level: "MEDIUM" },
]

const geographicAlerts = [
  { alert: "HIGH BIAS DETECTED", countries: "USA → Nigeria", model: "GPT4 HIRING ASSISTANT", severity: "HIGH", time: "2 min ago" },
  { alert: "CULTURAL FACTOR IMPACT", countries: "UK → India", model: "CREDIT SCORING V3", severity: "MEDIUM", time: "5 min ago" },
  { alert: "REGULATORY MISMATCH", countries: "Germany → Brazil", model: "CLAUDE LEGAL ADVISOR", severity: "LOW", time: "10 min ago" },
  { alert: "ECONOMIC BIAS PATTERN", countries: "Japan → Mexico", model: "FRAUD DETECTION V2", severity: "HIGH", time: "15 min ago" },
]

export function GeographicBiasDashboard() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">GEOGRAPHIC BIAS ANALYSIS</h1>
        <p className="text-sm text-muted-foreground font-mono">
          CROSS-COUNTRY CULTURAL FACTORS AND REGIONAL BIAS DETECTION
        </p>
      </div>

      {/* Geographic Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {geographicMetrics.map((metric) => (
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
            <Globe className="mr-2 h-4 w-4" />
            RUN CROSS-COUNTRY ANALYSIS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <Users2 className="mr-2 h-4 w-4" />
            ANALYZE CULTURAL FACTORS
          </Button>
          <Button variant="outline" className="bg-transparent">
            <MapPin className="mr-2 h-4 w-4" />
            REGIONAL BIAS MAPPING
          </Button>
        </div>
      </div>

      {/* Country Analysis Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Globe className="h-4 w-4" />
            CROSS-COUNTRY BIAS ANALYSIS
          </CardTitle>
          <CardDescription className="text-xs">SOURCE TO TARGET COUNTRY BIAS DETECTION</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SOURCE → TARGET</TableHead>
                  <TableHead>MODEL</TableHead>
                  <TableHead>BIAS SCORE</TableHead>
                  <TableHead>PERFORMANCE DROP</TableHead>
                  <TableHead>CULTURAL FACTORS</TableHead>
                  <TableHead>RISK LEVEL</TableHead>
                  <TableHead>ACTION</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {countryAnalyses.map((analysis, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono">
                      <div className="font-medium">{analysis.source} → {analysis.target}</div>
                    </TableCell>
                    <TableCell className="font-mono">{analysis.model}</TableCell>
                    <TableCell className="font-mono">{analysis.bias_score}</TableCell>
                    <TableCell className="font-mono">{analysis.performance_drop}%</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {analysis.cultural_factors.map((factor, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {factor}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        analysis.risk_level === "HIGH" ? "bg-red-100 text-red-800" :
                        analysis.risk_level === "MEDIUM" ? "bg-yellow-100 text-yellow-800" :
                        "bg-green-100 text-green-800"
                      }>
                        {analysis.risk_level}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button size="sm" variant="outline">
                          <Target className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <BarChart3 className="h-4 w-4" />
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

      {/* Cultural Factors Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Users2 className="h-4 w-4" />
            CULTURAL FACTORS ANALYSIS
          </CardTitle>
          <CardDescription className="text-xs">LANGUAGE ECONOMIC CULTURAL REGULATORY IMPACT</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {culturalFactors.map((factor, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    factor.impact === "HIGH" ? "bg-red-500" :
                    factor.impact === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{factor.factor}</div>
                    <div className="text-xs text-muted-foreground">Weight: {factor.weight} • Bias Contribution: {factor.bias_contribution}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">{factor.affected_countries.length} COUNTRIES</div>
                    <div className="text-xs text-muted-foreground">{factor.affected_countries.join(", ")}</div>
                  </div>
                  <Badge variant={factor.impact === "HIGH" ? "destructive" : "outline"}>
                    {factor.impact}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Regional Bias Patterns */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            REGIONAL BIAS PATTERNS
          </CardTitle>
          <CardDescription className="text-xs">GEOGRAPHIC REGION BIAS ANALYSIS</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {regionalBiasPatterns.map((region, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    region.risk_level === "HIGH" ? "bg-red-500" :
                    region.risk_level === "MEDIUM" ? "bg-yellow-500" : "bg-green-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{region.region}</div>
                    <div className="text-xs text-muted-foreground">{region.models_affected} models affected</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-sm font-mono">Bias: {region.bias_score}</div>
                    <div className="text-xs text-muted-foreground">Regional pattern</div>
                  </div>
                  <Badge variant={region.risk_level === "HIGH" ? "destructive" : "outline"}>
                    {region.risk_level}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Geographic Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            GEOGRAPHIC BIAS ALERTS
          </CardTitle>
          <CardDescription className="text-xs">REAL-TIME CROSS-COUNTRY BIAS DETECTION</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {geographicAlerts.map((alert, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`h-4 w-4 ${
                    alert.severity === "HIGH" ? "text-red-500" :
                    alert.severity === "MEDIUM" ? "text-yellow-500" : "text-blue-500"
                  }`} />
                  <div>
                    <div className="font-medium text-sm">{alert.alert}</div>
                    <div className="text-xs text-muted-foreground">{alert.countries} • {alert.model}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={alert.severity === "HIGH" ? "destructive" : "outline"}>
                    {alert.severity}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{alert.time}</span>
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
            <CardTitle className="text-sm">GEOGRAPHIC BIAS RADAR</CardTitle>
            <CardDescription className="text-xs">REGIONAL BIAS DETECTION PATTERNS</CardDescription>
          </CardHeader>
          <CardContent>
            <BiasDetectionRadar />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">BIAS DISTRIBUTION</CardTitle>
            <CardDescription className="text-xs">GEOGRAPHIC BIAS SCORE DISTRIBUTION</CardDescription>
          </CardHeader>
          <CardContent>
            <DistributionChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">CULTURAL FACTORS IMPACT</CardTitle>
            <CardDescription className="text-xs">CULTURAL FACTOR BIAS CONTRIBUTION</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {culturalFactors.map((factor, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{factor.factor}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${factor.bias_contribution * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{factor.bias_contribution}</span>
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
