"use client"

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { Badge } from '@/components/ui/common/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/common/tabs'
import { Alert, AlertDescription } from '@/components/ui/common/alert'
import { Skeleton } from '@/components/ui/common/loading-skeleton'
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Eye, 
  EyeOff,
  RefreshCw,
  Settings,
  TrendingUp,
  TrendingDown,
  Minus,
  Bell,
  BellOff,
  Zap,
  Cpu,
  HardDrive,
  MemoryStick,
  Network
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface ModelMetrics {
  model_id: string
  timestamp: string
  accuracy?: number
  bias_score?: number
  drift_score?: number
  latency?: number
  throughput?: number
  error_rate?: number
  custom_metrics?: Record<string, number>
}

interface Alert {
  id: string
  rule_id: string
  model_id: string
  metric: string
  value: number
  threshold: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  created_at: string
  acknowledged: boolean
  acknowledged_by?: string
  acknowledged_at?: string
}

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'critical'
  uptime: number
  memory_usage: number
  cpu_usage: number
  disk_usage: number
  active_connections: number
  last_check: string
  services: Record<string, string>
}

interface MonitoringConfig {
  model_id: string
  metrics: string[]
  thresholds: Record<string, number>
  frequency: number
  enabled: boolean
}

export const RealTimeMonitoringDashboard: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [metrics, setMetrics] = useState<Record<string, ModelMetrics[]>>({})
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [configs, setConfigs] = useState<Record<string, MonitoringConfig>>({})
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [showAcknowledged, setShowAcknowledged] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  // WebSocket connection management
  const connectWebSocket = useCallback((userId: string = 'default-user') => {
    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/monitoring/ws'
      const ws = new WebSocket(`${wsUrl}/${userId}`)
      
      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log('WebSocket connected')
        
        // Subscribe to all models
        Object.keys(configs).forEach(modelId => {
          ws.send(JSON.stringify({
            type: 'subscribe',
            model_id: modelId
          }))
        })
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }
      
      ws.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
        
        // Attempt to reconnect
        if (autoRefresh) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket(userId)
          }, 5000)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection failed')
      }
      
      wsRef.current = ws
    } catch (e) {
      console.error('Error connecting to WebSocket:', e)
      setError('Failed to connect to monitoring service')
    }
  }, [configs, autoRefresh])

  const handleWebSocketMessage = useCallback((data: any) => {
    if (data.type === 'metrics') {
      setMetrics(prev => ({
        ...prev,
        [data.data.model_id]: [...(prev[data.data.model_id] || []), data.data].slice(-100)
      }))
    } else if (data.type === 'alert') {
      setAlerts(prev => [data.data, ...prev].slice(0, 100))
    } else if (data.type === 'health') {
      setSystemHealth(data.data)
    }
  }, [])

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setIsLoading(true)
        
        // Load monitoring configurations
        const configsResponse = await fetch('/api/v1/monitoring/config')
        if (configsResponse.ok) {
          const configsData = await configsResponse.json()
          setConfigs(configsData.data || {})
        }
        
        // Load recent alerts
        const alertsResponse = await fetch('/api/v1/monitoring/alerts?limit=50')
        if (alertsResponse.ok) {
          const alertsData = await alertsResponse.json()
          setAlerts(alertsData.data || [])
        }
        
        // Load system health
        const healthResponse = await fetch('/api/v1/monitoring/health')
        if (healthResponse.ok) {
          const healthData = await healthResponse.json()
          setSystemHealth(healthData.data)
        }
        
        setIsLoading(false)
      } catch (e) {
        console.error('Error loading initial data:', e)
        setError('Failed to load monitoring data')
        setIsLoading(false)
      }
    }
    
    loadInitialData()
  }, [])

  // Connect to WebSocket when configs are loaded
  useEffect(() => {
    if (Object.keys(configs).length > 0) {
      connectWebSocket()
    }
  }, [configs, connectWebSocket])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'current-user' })
      })
      
      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, acknowledged: true, acknowledged_by: 'current-user', acknowledged_at: new Date().toISOString() }
            : alert
        ))
      }
    } catch (e) {
      console.error('Error acknowledging alert:', e)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100'
      case 'degraded': return 'text-yellow-600 bg-yellow-100'
      case 'critical': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500 text-white'
      case 'high': return 'bg-orange-500 text-white'
      case 'medium': return 'bg-yellow-500 text-white'
      case 'low': return 'bg-blue-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="w-4 h-4 text-green-500" />
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-500" />
    return <Minus className="w-4 h-4 text-gray-500" />
  }

  const filteredAlerts = alerts.filter(alert => 
    showAcknowledged || !alert.acknowledged
  )

  if (isLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Real-Time Monitoring Dashboard</h1>
          <p className="text-gray-600">Live model performance and system health monitoring</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className={cn(
            'flex items-center space-x-1',
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          )}>
            {isConnected ? <CheckCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            {autoRefresh ? 'Auto' : 'Manual'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Model Metrics</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* System Health Summary */}
          {systemHealth && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>System Health</span>
                  <Badge className={getStatusColor(systemHealth.status)}>
                    {systemHealth.status.toUpperCase()}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-blue-500" />
                    <div>
                      <p className="text-sm text-gray-600">CPU</p>
                      <p className="font-semibold">{systemHealth.cpu_usage.toFixed(1)}%</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <MemoryStick className="w-4 h-4 text-green-500" />
                    <div>
                      <p className="text-sm text-gray-600">Memory</p>
                      <p className="font-semibold">{systemHealth.memory_usage.toFixed(1)}%</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <HardDrive className="w-4 h-4 text-purple-500" />
                    <div>
                      <p className="text-sm text-gray-600">Disk</p>
                      <p className="font-semibold">{systemHealth.disk_usage.toFixed(1)}%</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Network className="w-4 h-4 text-orange-500" />
                    <div>
                      <p className="text-sm text-gray-600">Connections</p>
                      <p className="font-semibold">{systemHealth.active_connections}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="w-5 h-5" />
                <span>Recent Alerts</span>
                <Badge variant="secondary">{filteredAlerts.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredAlerts.slice(0, 5).map(alert => (
                  <div key={alert.id} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex items-center space-x-2">
                      <Badge className={getSeverityColor(alert.severity)}>
                        {alert.severity}
                      </Badge>
                      <span className="text-sm">{alert.message}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </span>
                      {!alert.acknowledged && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          {/* Model Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Model Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.keys(configs).map(modelId => {
                  const modelMetrics = metrics[modelId] || []
                  const latestMetrics = modelMetrics[modelMetrics.length - 1]
                  const previousMetrics = modelMetrics[modelMetrics.length - 2]
                  
                  return (
                    <Card key={modelId} className="cursor-pointer hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold">{modelId}</h3>
                          <Badge variant={configs[modelId]?.enabled ? "default" : "secondary"}>
                            {configs[modelId]?.enabled ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                        
                        {latestMetrics ? (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">Accuracy</span>
                              <div className="flex items-center space-x-1">
                                <span className="font-semibold">
                                  {(latestMetrics.accuracy * 100).toFixed(1)}%
                                </span>
                                {previousMetrics && getTrendIcon(
                                  latestMetrics.accuracy || 0,
                                  previousMetrics.accuracy || 0
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">Latency</span>
                              <span className="font-semibold">
                                {latestMetrics.latency?.toFixed(1)}ms
                              </span>
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">Error Rate</span>
                              <span className="font-semibold">
                                {(latestMetrics.error_rate * 100).toFixed(2)}%
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="text-center text-gray-500 py-4">
                            No metrics available
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <Bell className="w-5 h-5" />
                  <span>Alerts</span>
                  <Badge variant="secondary">{filteredAlerts.length}</Badge>
                </CardTitle>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAcknowledged(!showAcknowledged)}
                  >
                    {showAcknowledged ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    {showAcknowledged ? 'Show All' : 'Show Unacknowledged'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredAlerts.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    No alerts found
                  </div>
                ) : (
                  filteredAlerts.map(alert => (
                    <div key={alert.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge className={getSeverityColor(alert.severity)}>
                              {alert.severity}
                            </Badge>
                            <span className="text-sm font-medium">{alert.model_id}</span>
                            {alert.acknowledged && (
                              <Badge variant="outline">Acknowledged</Badge>
                            )}
                          </div>
                          <p className="text-sm mb-2">{alert.message}</p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>Metric: {alert.metric}</span>
                            <span>Value: {alert.value.toFixed(3)}</span>
                            <span>Threshold: {alert.threshold.toFixed(3)}</span>
                            <span>{new Date(alert.created_at).toLocaleString()}</span>
                          </div>
                        </div>
                        {!alert.acknowledged && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => acknowledgeAlert(alert.id)}
                          >
                            Acknowledge
                          </Button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          {systemHealth && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>System Health Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* System Metrics */}
                  <div className="space-y-4">
                    <h3 className="font-semibold">System Metrics</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Status</span>
                        <Badge className={getStatusColor(systemHealth.status)}>
                          {systemHealth.status.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Uptime</span>
                        <span className="font-semibold">
                          {Math.floor(systemHealth.uptime / 3600)}h {Math.floor((systemHealth.uptime % 3600) / 60)}m
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Last Check</span>
                        <span className="font-semibold">
                          {new Date(systemHealth.last_check).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Service Status */}
                  <div className="space-y-4">
                    <h3 className="font-semibold">Service Status</h3>
                    <div className="space-y-2">
                      {Object.entries(systemHealth.services).map(([service, status]) => (
                        <div key={service} className="flex items-center justify-between">
                          <span className="text-sm capitalize">{service}</span>
                          <Badge className={getStatusColor(status)}>
                            {status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
