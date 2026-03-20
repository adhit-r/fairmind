'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'

type MonitoringAlert = {
  id?: string
  type?: string
  severity?: string
  message?: string
  created_at?: string
  timestamp?: string
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get<any>(API_ENDPOINTS.monitoring.alerts, {
        enableRetry: true,
        maxRetries: 2,
        timeout: 10000,
      })

      if (response.success) {
        const payload = (response.data as any) ?? []
        const list = Array.isArray(payload)
          ? payload
          : Array.isArray(payload?.data)
            ? payload.data
            : []
        setAlerts(list)
      } else {
        setAlerts([])
        setError(response.error || 'Failed to load alerts')
      }
    } catch (e) {
      setAlerts([])
      setError(e instanceof Error ? e.message : 'Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAlerts()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Alerts</h1>
          <p className="text-muted-foreground mt-1">System and model monitoring alerts</p>
        </div>
        <Button onClick={loadAlerts}>
          <IconRefresh className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert className="border-2 border-yellow-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Alerts Unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card className="p-6 border-2 border-black shadow-brutal">
        {loading ? (
          <p>Loading alerts...</p>
        ) : alerts.length === 0 ? (
          <p className="text-muted-foreground">No active alerts.</p>
        ) : (
          <div className="space-y-3">
            {alerts.map((a, idx) => (
              <div key={a.id || `${a.type || 'alert'}-${idx}`} className="border-2 border-black p-3">
                <div className="font-bold uppercase text-sm">{a.severity || 'info'} - {a.type || 'alert'}</div>
                <div>{a.message || 'No message'}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {a.created_at || a.timestamp || 'timestamp unavailable'}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

