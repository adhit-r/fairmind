import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { History, Clock, CheckCircle, AlertTriangle } from "lucide-react"

export default function SimulationHistoryPage() {
  const simulations = [
    {
      id: "sim-001",
      name: "Bias Detection Simulation",
      model: "GPT-4",
      status: "Completed",
      duration: "5m 30s",
      date: "2024-01-15"
    },
    {
      id: "sim-002",
      name: "Adversarial Attack Test",
      model: "ResNet-50", 
      status: "Failed",
      duration: "2m 15s",
      date: "2024-01-14"
    },
    {
      id: "sim-003",
      name: "Privacy Impact Assessment",
      model: "Claude-3",
      status: "Completed",
      duration: "8m 45s",
      date: "2024-01-13"
    }
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Simulation History</h1>
        <p className="text-muted-foreground">
          View past simulation results and analysis
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Simulations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {simulations.map((sim) => (
              <div key={sim.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div>
                    <h3 className="font-medium">{sim.name}</h3>
                    <p className="text-sm text-muted-foreground">Model: {sim.model} • {sim.date}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-sm font-medium">{sim.duration}</div>
                  </div>
                  <Badge className={
                    sim.status === "Completed" ? "bg-green-100 text-green-800" :
                    sim.status === "Failed" ? "bg-red-100 text-red-800" :
                    "bg-yellow-100 text-yellow-800"
                  }>
                    {sim.status}
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