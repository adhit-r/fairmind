"use client"

import * as React from "react"
import { 
  Line, 
  LineChart, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer, 
  ReferenceLine, 
  Tooltip, 
  Legend
} from "recharts"
import { Skeleton } from "@/components/ui/common/skeleton"
import { AlertTriangle, AlertCircle, CheckCircle, Info } from "lucide-react"

type DriftType = 'data_drift' | 'concept_drift' | 'prediction_drift' | 'feature_drift'

interface DriftDataPoint {
  timestamp: string
  data_drift: number
  concept_drift: number
  prediction_drift: number
  feature_drift: number
}

const DRIFT_NAMES: Record<DriftType, string> = {
  data_drift: 'Data Drift',
  concept_drift: 'Concept Drift',
  prediction_drift: 'Prediction Drift',
  feature_drift: 'Feature Drift'
}

const DRIFT_COLORS: Record<DriftType, string> = {
  data_drift: '#8884d8',
  concept_drift: '#82ca9d',
  prediction_drift: '#ffc658',
  feature_drift: '#ff7300'
}

const DRIFT_THRESHOLD = 0.1

const getDriftSeverity = (value: number) => {
  if (value >= DRIFT_THRESHOLD) return 'high'
  if (value >= 0.08) return 'medium'
  return 'low'
}

const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
  return {
    high: 'text-red-600',
    medium: 'text-amber-600',
    low: 'text-green-600'
  }[severity]
}

export function ModelDriftMonitor() {
  const [data, setData] = React.useState<DriftDataPoint[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const fetchDriftData = async () => {
      try {
        setLoading(true)
        await new Promise(resolve => setTimeout(resolve, 800))
        
        const mockData: DriftDataPoint[] = [
          { timestamp: "00:00", data_drift: 0.02, concept_drift: 0.01, prediction_drift: 0.03, feature_drift: 0.02 },
          { timestamp: "04:00", data_drift: 0.03, concept_drift: 0.02, prediction_drift: 0.04, feature_drift: 0.03 },
          { timestamp: "08:00", data_drift: 0.05, concept_drift: 0.03, prediction_drift: 0.06, feature_drift: 0.04 },
          { timestamp: "12:00", data_drift: 0.08, concept_drift: 0.05, prediction_drift: 0.09, feature_drift: 0.07 },
          { timestamp: "16:00", data_drift: 0.12, concept_drift: 0.08, prediction_drift: 0.13, feature_drift: 0.11 },
          { timestamp: "20:00", data_drift: 0.15, concept_drift: 0.11, prediction_drift: 0.16, feature_drift: 0.14 },
          { timestamp: "24:00", data_drift: 0.18, concept_drift: 0.13, prediction_drift: 0.19, feature_drift: 0.17 },
        ]
        
        setData(mockData)
        setError(null)
      } catch (err) {
        console.error('Failed to load drift data:', err)
        setError('Failed to load model drift data')
      } finally {
        setLoading(false)
      }
    }

    fetchDriftData()
  }, [])

  if (loading) {
    return (
      <div className="w-full h-full">
        <div className="space-y-4">
          <Skeleton className="h-6 w-56" />
          <Skeleton className="h-[250px] w-full" />
          <div className="flex justify-center gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-4 w-20" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full h-full">
        <div className="flex items-center gap-2 p-4 text-red-500 rounded-md bg-red-50">
          <Info className="w-4 h-4" />
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  const latestData = data.length > 0 ? data[data.length - 1] : null

  return (
    <div className="w-full h-full">
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis 
              dataKey="timestamp" 
              stroke="#666" 
              fontSize={10} 
              tickLine={false}
            />
            <YAxis 
              stroke="#666" 
              fontSize={10} 
              tickFormatter={(value) => value.toFixed(2)}
              domain={[0, 0.25]}
              tickCount={6}
              tickLine={false}
            />
            <Tooltip />
            <Legend />
            <ReferenceLine y={DRIFT_THRESHOLD} stroke="#ef4444" strokeDasharray="5 5" />
            
            <Line
              type="monotone"
              name="Data Drift"
              dataKey="data_drift"
              stroke={DRIFT_COLORS.data_drift}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              name="Concept Drift"
              dataKey="concept_drift"
              stroke={DRIFT_COLORS.concept_drift}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              name="Prediction Drift"
              dataKey="prediction_drift"
              stroke={DRIFT_COLORS.prediction_drift}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              name="Feature Drift"
              dataKey="feature_drift"
              stroke={DRIFT_COLORS.feature_drift}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {latestData && (
        <div className="mt-6">
          <h4 className="text-sm font-medium mb-3">Drift Status</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(Object.keys(DRIFT_NAMES) as DriftType[]).map((driftType) => {
              const value = latestData[driftType]
              const severity = getDriftSeverity(value)
              
              return (
                <div 
                  key={driftType}
                  className="p-3 rounded-lg border"
                >
                  <div className="flex items-center justify-between mb-1">
                    <h5 className="text-xs font-medium">{DRIFT_NAMES[driftType]}</h5>
                    <div className={`text-xs font-mono font-bold ${getSeverityColor(severity)}`}>
                      {value.toFixed(4)}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="capitalize">
                      {severity} Risk
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
      
      <div className="mt-4 text-xs text-muted-foreground font-mono flex justify-between items-center">
        <span>Last updated: {new Date().toLocaleString()}</span>
        <span className="text-[10px] opacity-70">
          Threshold: {DRIFT_THRESHOLD.toFixed(2)} (High Risk)
        </span>
      </div>
    </div>
  )
}
