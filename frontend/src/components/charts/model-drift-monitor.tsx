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
  TooltipProps,
  Legend,
  LegendProps,
  ReferenceLineProps
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
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

const DRIFT_DESCRIPTIONS: Record<DriftType, string> = {
  data_drift: 'Measures changes in input data distribution',
  concept_drift: 'Measures changes in relationships between inputs and outputs',
  prediction_drift: 'Measures changes in model prediction distribution',
  feature_drift: 'Measures changes in individual feature distributions'
}

const DRIFT_COLORS: Record<DriftType, string> = {
  data_drift: 'hsl(var(--chart-1))',
  concept_drift: 'hsl(var(--chart-2))',
  prediction_drift: 'hsl(var(--chart-3))',
  feature_drift: 'hsl(var(--chart-4))'
}

const DRIFT_THRESHOLD = 0.1
const WARNING_THRESHOLD = 0.08

const getDriftSeverity = (value: number) => {
  if (value >= DRIFT_THRESHOLD) return 'high'
  if (value >= WARNING_THRESHOLD) return 'medium'
  return 'low'
}

const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
  return {
    high: 'text-red-600 dark:text-red-400',
    medium: 'text-amber-600 dark:text-amber-400',
    low: 'text-green-600 dark:text-green-400'
  }[severity]
}

const getSeverityIcon = (severity: 'high' | 'medium' | 'low') => {
  const className = 'w-4 h-4 flex-shrink-0'
  
  return {
    high: <AlertTriangle className={`${className} text-red-500`} />,
    medium: <AlertCircle className={`${className} text-amber-500`} />,
    low: <CheckCircle className={`${className} text-green-500`} />
  }[severity]
}

interface CustomTooltipProps extends TooltipProps<number, string> {
  active?: boolean
  payload?: Array<{
    name: string
    value: number
    dataKey: string
    color: string
  }>
  label?: string
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null
  
  return (
    <Card className="p-4 shadow-lg">
      <h4 className="text-sm font-medium mb-3">
        {label} - Drift Analysis
      </h4>
      <div className="space-y-2">
        {payload.map((item) => {
          const driftType = item.dataKey as DriftType
          const severity = getDriftSeverity(item.value)
          
          return (
            <div key={item.name} className="flex items-start justify-between">
              <div className="flex items-start gap-2">
                <div 
                  className="w-3 h-3 rounded-full flex-shrink-0 mt-1" 
                  style={{ backgroundColor: item.color }}
                />
                <div>
                  <p className="text-sm font-medium">{DRIFT_NAMES[driftType]}</p>
                  <p className="text-xs text-muted-foreground">
                    {DRIFT_DESCRIPTIONS[driftType]}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-mono font-bold ${getSeverityColor(severity)}`}>
                  {item.value.toFixed(4)}
                </span>
                {getSeverityIcon(severity)}
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

interface CustomLegendProps extends LegendProps {
  payload?: Array<{
    value: string
    color: string
    payload?: {
      data?: Array<{
        [key in DriftType]?: number
      }>
    }
  }>
}

const CustomLegend: React.FC<CustomLegendProps> = ({ payload }) => {
  if (!payload || payload.length === 0) return null
  
  return (
    <div className="flex flex-wrap justify-center gap-4 mt-4">
      {payload.map((entry, index: number) => {
        if (!entry.value) return null
        
        const driftType = entry.value as DriftType
        const value = entry.payload?.data?.[0]?.[driftType]
        const severity = value !== undefined ? getDriftSeverity(value) : 'low'
        
        return (
          <div key={`legend-${index}`} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-xs font-mono">
              {DRIFT_NAMES[driftType] || entry.value}
              {value !== undefined && (
                <span className={`ml-1 ${getSeverityColor(severity)}`}>
                  ({value.toFixed(2)})
                </span>
              )}
            </span>
          </div>
        )
      })}
    </div>
  )
}

const CustomReferenceLine: React.FC<Omit<ReferenceLineProps, 'ref'>> = (props) => {
  return (
    <ReferenceLine 
      {...props} 
      stroke="hsl(var(--destructive))"
      strokeDasharray="5 5"
      label={({ viewBox }: { viewBox: { x: number; y: number } }) => (
        <text
          x={viewBox.x}
          y={viewBox.y - 10}
          fill="hsl(var(--destructive))"
          fontSize={10}
          fontFamily="JetBrains Mono"
          textAnchor="middle"
        >
          Drift Threshold
        </text>
      )}
    />
  )
}

export function ModelDriftMonitor() {
  const [data, setData] = React.useState<DriftDataPoint[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [selectedDrift, setSelectedDrift] = React.useState<DriftType | 'all'>('all')

  // Calculate drift statistics
  const driftStats = React.useMemo(() => {
    if (data.length === 0) return null
    
    const latest = data[data.length - 1]
    const stats: Record<DriftType, { current: number; trend: 'up' | 'down' | 'stable' }> = {
      data_drift: { current: 0, trend: 'stable' },
      concept_drift: { current: 0, trend: 'stable' },
      prediction_drift: { current: 0, trend: 'stable' },
      feature_drift: { current: 0, trend: 'stable' }
    }
    
    // Calculate current values and trends
    Object.keys(stats).forEach((key) => {
      const driftKey = key as DriftType
      const values = data.map(d => d[driftKey])
      stats[driftKey].current = values[values.length - 1]
      
      // Simple trend detection (compare last 3 points)
      if (values.length >= 3) {
        const lastThree = values.slice(-3)
        const avgFirstHalf = (lastThree[0] + lastThree[1]) / 2
        const avgSecondHalf = (lastThree[1] + lastThree[2]) / 2
        
        if (avgSecondHalf > avgFirstHalf * 1.1) {
          stats[driftKey].trend = 'up'
        } else if (avgSecondHalf < avgFirstHalf * 0.9) {
          stats[driftKey].trend = 'down'
        }
      }
    })
    
    return stats
  }, [data])

  // Fetch drift data
  React.useEffect(() => {
    const fetchDriftData = async () => {
      try {
        setLoading(true)
        
        // Simulate API call with timeout
        await new Promise(resolve => setTimeout(resolve, 800))
        
        // Mock data - in a real app, this would come from an API
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
        setError('Failed to load model drift data. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    fetchDriftData()
  }, [])

  // Filter data based on selected drift type
  const filteredData = React.useMemo(() => {
    if (selectedDrift === 'all') return data
    
    return data.map(item => ({
      timestamp: item.timestamp,
      [selectedDrift]: item[selectedDrift]
    }))
  }, [data, selectedDrift])

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-mono">MODEL_DRIFT_MONITOR</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-6 w-56" />
            <Skeleton className="h-[250px] w-full" />
            <div className="flex justify-center gap-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-4 w-20" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-mono">MODEL_DRIFT_MONITOR</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 p-4 text-red-500 rounded-md bg-red-50 dark:bg-red-900/20">
            <Info className="w-4 h-4 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Get the latest drift values
  const latestData = data.length > 0 ? data[data.length - 1] : null
  const hasHighDrift = latestData && Object.values(latestData).some(
    (value, i) => i > 0 && value >= DRIFT_THRESHOLD
  )

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <CardTitle className="text-sm font-mono">MODEL_DRIFT_MONITOR</CardTitle>
          {hasHighDrift && (
            <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-4 h-4" />
              <span>High drift detected</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={filteredData}
              margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
            >
              <defs>
                {Object.entries(DRIFT_COLORS).map(([key, color]) => (
                  <linearGradient key={key} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={color} stopOpacity={0.1} />
                    <stop offset="95%" stopColor={color} stopOpacity={0.01} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="hsl(var(--border))" 
                vertical={false}
              />
              <XAxis 
                dataKey="timestamp" 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={10} 
                fontFamily="JetBrains Mono"
                tickLine={false}
                axisLine={{ stroke: 'hsl(var(--border))' }}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))" 
                fontSize={10} 
                fontFamily="JetBrains Mono" 
                tickFormatter={(value) => value.toFixed(2)}
                domain={[0, 0.25]}
                tickCount={6}
                tickLine={false}
                axisLine={{ stroke: 'hsl(var(--border))' }}
              />
              <Tooltip 
                content={<CustomTooltip />} 
                cursor={{ stroke: 'hsl(var(--border))', strokeDasharray: '3 3' }}
              />
              <Legend 
                content={<CustomLegend />}
                wrapperStyle={{ marginTop: '10px' }}
              />
              
              <CustomReferenceLine y={DRIFT_THRESHOLD} />
              
              {(selectedDrift === 'all' 
                ? Object.keys(DRIFT_NAMES) 
                : [selectedDrift]
              ).map((driftKey) => {
                const key = driftKey as DriftType
                const severity = latestData ? getDriftSeverity(latestData[key]) : 'low'
                
                return (
                  <Line
                    key={key}
                    type="monotone"
                    name={DRIFT_NAMES[key]}
                    dataKey={key}
                    stroke={DRIFT_COLORS[key]}
                    strokeWidth={2}
                    dot={false}
                    strokeDasharray={severity === 'high' ? '5 5' : undefined}
                    activeDot={{
                      r: 6,
                      stroke: DRIFT_COLORS[key],
                      strokeWidth: 2,
                      fill: 'hsl(var(--background))',
                      strokeDasharray: severity === 'high' ? '3 3' : undefined
                    }}
                    isAnimationActive={!loading}
                  />
                )
              })}
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {latestData && driftStats && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-3">Drift Status</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {(Object.keys(DRIFT_NAMES) as DriftType[]).map((driftType) => {
                const value = latestData[driftType]
                const severity = getDriftSeverity(value)
                const trend = driftStats[driftType].trend
                const trendText = {
                  up: '↑ Increasing',
                  down: '↓ Decreasing',
                  stable: '→ Stable'
                }[trend]
                
                return (
                  <div 
                    key={driftType}
                    className={`p-3 rounded-lg border ${
                      severity === 'high' 
                        ? 'bg-red-50/50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30' 
                        : severity === 'medium' 
                          ? 'bg-amber-50/50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-900/30' 
                          : 'bg-green-50/50 dark:bg-green-900/10 border-green-200 dark:border-green-900/30'
                    }`}
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
                      <span className={
                        trend === 'up' 
                          ? 'text-red-500' 
                          : trend === 'down' 
                            ? 'text-green-500' 
                            : 'text-muted-foreground'
                      }>
                        {trendText}
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
      </CardContent>
    </Card>
  )
}
