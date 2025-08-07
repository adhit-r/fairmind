import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Zap, Play, Clock, CheckCircle } from "lucide-react"

export default function SimulationPage() {
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">New Simulation</h1>
          <p className="text-muted-foreground">
            Create and run AI model simulations
          </p>
        </div>
        <Button>
          <Play className="mr-2 h-4 w-4" />
          Start Simulation
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Simulation Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Simulation configuration options will be available here.
          </p>
        </CardContent>
      </Card>
    </div>
  )
} 