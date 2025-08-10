"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Clock, FileText, BarChart3 } from "lucide-react"

interface SimulationRun {
  id: string
  model_name: string
  created_at: string
  status: "completed" | "failed" | "running"
  metrics?: {
    performance?: {
      accuracy?: number
      precision_macro?: number
      recall_macro?: number
      f1_macro?: number
    }
    fairness?: {
      by_attribute?: Array<{
        attribute: string
        demographic_parity_difference: number
      }>
    }
  }
}

interface SimulationHistoryProps {
  runs?: SimulationRun[]
  onViewDetails?: (run: SimulationRun) => void
}

export function SimulationHistory({ runs, onViewDetails }: SimulationHistoryProps) {
  if (!runs || runs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Simulation History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            No simulation runs yet.
          </div>
        </CardContent>
      </Card>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Recent Simulations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {runs.slice(0, 5).map((run) => (
            <div key={run.id} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex flex-col">
                  <div className="font-medium text-sm">{run.model_name}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatDate(run.created_at)}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {run.metrics?.performance?.accuracy && (
                  <div className="text-xs text-muted-foreground">
                    Acc: {Math.round(run.metrics.performance.accuracy * 100)}%
                  </div>
                )}
                
                <Badge className={getStatusColor(run.status)}>
                  {run.status}
                </Badge>
                
                {onViewDetails && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onViewDetails(run)}
                    className="h-7 px-2"
                  >
                    <BarChart3 className="h-3 w-3 mr-1" />
                    View
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
        
        {runs.length > 5 && (
          <div className="mt-4 pt-4 border-t text-center">
            <Button variant="outline" size="sm">
              View All ({runs.length} total)
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
