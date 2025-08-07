import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TestTube, Play, Clock, CheckCircle } from "lucide-react"

export default function TestingPage() {
  const tests = [
    {
      id: "test-001",
      name: "Bias Detection Test",
      model: "GPT-4",
      status: "Running",
      progress: 75,
      duration: "2m 30s"
    },
    {
      id: "test-002", 
      name: "Adversarial Attack Test",
      model: "ResNet-50",
      status: "Completed",
      progress: 100,
      duration: "1m 45s"
    },
    {
      id: "test-003",
      name: "Privacy Impact Assessment",
      model: "Claude-3",
      status: "Pending",
      progress: 0,
      duration: "0s"
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">AI Model Testing</h1>
          <p className="text-muted-foreground">
            Comprehensive testing suite for AI models
          </p>
        </div>
        <Button>
          <Play className="mr-2 h-4 w-4" />
          New Test
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tests</CardTitle>
            <TestTube className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tests.length}</div>
            <p className="text-xs text-muted-foreground">
              Test suites
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {tests.filter(t => t.status === "Running").length}
            </div>
            <p className="text-xs text-muted-foreground">
              In progress
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {tests.filter(t => t.status === "Completed").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Successfully finished
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <TestTube className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {tests.filter(t => t.status === "Pending").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Queued for execution
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Test Suite</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tests.map((test) => (
              <div key={test.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div>
                    <h3 className="font-medium">{test.name}</h3>
                    <p className="text-sm text-muted-foreground">Model: {test.model}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-sm font-medium">{test.progress}%</div>
                    <div className="text-xs text-muted-foreground">{test.duration}</div>
                  </div>
                  <Badge className={
                    test.status === "Running" ? "bg-orange-100 text-orange-800" :
                    test.status === "Completed" ? "bg-green-100 text-green-800" :
                    "bg-blue-100 text-blue-800"
                  }>
                    {test.status}
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