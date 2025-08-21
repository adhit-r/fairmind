"use client"

import { Area, AreaChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const data = [
  { time: "00:00", bias_score: 78, drift_score: 92, explainability: 70 },
  { time: "04:00", bias_score: 76, drift_score: 89, explainability: 72 },
  { time: "08:00", bias_score: 79, drift_score: 91, explainability: 68 },
  { time: "12:00", bias_score: 74, drift_score: 88, explainability: 71 },
  { time: "16:00", bias_score: 77, drift_score: 90, explainability: 69 },
  { time: "20:00", bias_score: 75, drift_score: 87, explainability: 73 },
  { time: "24:00", bias_score: 78, drift_score: 92, explainability: 70 },
]

export function TimeSeriesChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Time Series Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          <p>Time series chart loading...</p>
        </div>
      </CardContent>
    </Card>
  )
}
