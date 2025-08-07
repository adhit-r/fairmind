import { GeographicBiasDetector } from "@/components/geographic-bias-detector"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"

export default function GeographicBiasPage() {
  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Geographic Bias Detection</h1>
          <p className="text-muted-foreground">
            Analyze cross-country AI model performance and detect geographic bias
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          AI Governance
        </Badge>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Models</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">47</div>
            <p className="text-xs text-muted-foreground">Models analyzed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bias Detected</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">12</div>
            <p className="text-xs text-muted-foreground">Models with bias</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">5</div>
            <p className="text-xs text-muted-foreground">Critical deployments</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Countries</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-xs text-muted-foreground">Countries analyzed</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="analyzer" className="space-y-4">
        <TabsList>
          <TabsTrigger value="analyzer">Bias Analyzer</TabsTrigger>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="recent">Recent Analyses</TabsTrigger>
        </TabsList>

        <TabsContent value="analyzer" className="space-y-4">
          <GeographicBiasDetector />
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-4">
          <GeographicBiasDashboard />
        </TabsContent>

        <TabsContent value="recent" className="space-y-4">
          <RecentAnalyses />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function GeographicBiasDashboard() {
  return (
    <div className="space-y-6">
      {/* Risk Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Distribution</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">32</div>
              <div className="text-sm text-muted-foreground">Low Risk</div>
              <Progress value={68} className="mt-2" />
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">8</div>
              <div className="text-sm text-muted-foreground">Medium Risk</div>
              <Progress value={17} className="mt-2" />
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">5</div>
              <div className="text-sm text-muted-foreground">High Risk</div>
              <Progress value={11} className="mt-2" />
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">2</div>
              <div className="text-sm text-muted-foreground">Critical</div>
              <Progress value={4} className="mt-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Country Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Country Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { country: "USA", bias: 0.15, status: "COMPLIANT", models: 12 },
              { country: "India", bias: 0.45, status: "WARNING", models: 8 },
              { country: "Japan", bias: 0.72, status: "NON_COMPLIANT", models: 6 },
              { country: "Brazil", bias: 0.38, status: "WARNING", models: 5 },
              { country: "Germany", bias: 0.22, status: "COMPLIANT", models: 7 },
            ].map((item) => (
              <div key={item.country} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="font-medium">{item.country}</div>
                  <Badge variant={item.status === "COMPLIANT" ? "default" : item.status === "WARNING" ? "secondary" : "destructive"}>
                    {item.status}
                  </Badge>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-muted-foreground">{item.models} models</div>
                  <div className="text-sm font-medium">{(item.bias * 100).toFixed(1)}% bias</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert className="border-red-200 bg-red-50">
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <span>Critical bias detected in credit-scoring-v1 (USA → India)</span>
                  <Badge variant="destructive">CRITICAL</Badge>
                </div>
              </AlertDescription>
            </Alert>
            <Alert className="border-orange-200 bg-orange-50">
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <span>High bias detected in fraud-detection-v2 (UK → Brazil)</span>
                  <Badge variant="secondary">HIGH</Badge>
                </div>
              </AlertDescription>
            </Alert>
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <span>Medium bias detected in recommendation-engine-v1 (USA → Japan)</span>
                  <Badge variant="outline">MEDIUM</Badge>
                </div>
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function RecentAnalyses() {
  const recentAnalyses = [
    {
      id: "1",
      model_id: "credit-scoring-v1",
      source_country: "USA",
      target_country: "India",
      bias_score: 0.72,
      risk_level: "HIGH",
      timestamp: "2024-12-05T15:30:00Z",
      performance_drop: 12.5
    },
    {
      id: "2",
      model_id: "fraud-detection-v2",
      source_country: "UK",
      target_country: "Brazil",
      bias_score: 0.45,
      risk_level: "MEDIUM",
      timestamp: "2024-12-05T13:15:00Z",
      performance_drop: 8.2
    },
    {
      id: "3",
      model_id: "recommendation-engine-v1",
      source_country: "USA",
      target_country: "Japan",
      bias_score: 0.89,
      risk_level: "CRITICAL",
      timestamp: "2024-12-05T11:45:00Z",
      performance_drop: 18.7
    }
  ]

  return (
    <div className="space-y-4">
      {recentAnalyses.map((analysis) => (
        <Card key={analysis.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">{analysis.model_id}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {analysis.source_country} → {analysis.target_country}
                </p>
              </div>
              <Badge 
                variant={
                  analysis.risk_level === "CRITICAL" ? "destructive" :
                  analysis.risk_level === "HIGH" ? "secondary" :
                  analysis.risk_level === "MEDIUM" ? "outline" : "default"
                }
              >
                {analysis.risk_level}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm font-medium text-muted-foreground">Bias Score</div>
                <div className="text-2xl font-bold text-blue-600">{(analysis.bias_score * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">Performance Drop</div>
                <div className="text-2xl font-bold text-orange-600">{analysis.performance_drop}%</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">Analysis Date</div>
                <div className="text-sm">{new Date(analysis.timestamp).toLocaleDateString()}</div>
              </div>
            </div>
            <div className="mt-4 flex space-x-2">
              <Button variant="outline" size="sm">View Details</Button>
              <Button variant="outline" size="sm">Export Report</Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
} 