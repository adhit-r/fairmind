'use client'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useSystemHealth } from '@/lib/api/hooks/useMonitoring'

export default function StatusPage() {
  const { health, loading, error, refetch } = useSystemHealth()
  const checkedAt = health?.timestamp && new Date(health.timestamp)
  const services = health?.services && typeof health.services === 'object' && !Array.isArray(health.services)
    ? Object.entries(health.services) : []

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[30px] font-semibold tracking-[-.03em]">System Status</h1>
          <p className="mt-1 text-muted-foreground">Governance API · <code className="break-all">{API_ENDPOINTS.aiGovernance.status}</code></p>
        </div>
        <Button onClick={refetch} disabled={loading}>{error ? 'Retry' : 'Refresh'}</Button>
      </header>

      {loading ? <p role="status">Checking the governance API…</p> : error ? (
        <Alert>
          <AlertTitle>Governance API status unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : health && (
        <>
          <Card className="fm-card p-6">
            <h2 className="mb-4 text-xl font-semibold">Governance API response</h2>
            <dl className="grid gap-4 sm:grid-cols-2">
              <div><dt>Reported status</dt><dd className="font-semibold">{health.status}</dd></div>
              <div>
                <dt>Observation time</dt>
                <dd>{checkedAt && Number.isFinite(checkedAt.getTime()) ? (
                  <time dateTime={health.timestamp}>{checkedAt.toLocaleString()}</time>
                ) : 'Unreported'}</dd>
              </div>
            </dl>
          </Card>
          <Card className="fm-card p-6">
            <h2 className="mb-3 text-xl font-semibold">Service probes</h2>
            {services.length === 0 ? (
              <p className="text-muted-foreground">Individual service probes were not reported.</p>
            ) : (
              <ul className="divide-y">
                {services.map(([name, probe]) => {
                  const details = probe && typeof probe === 'object' ? probe : null
                  const status = typeof probe === 'string' ? probe : details?.status
                  const response = details?.responseTime ?? details?.response_time
                  return (
                    <li key={name} className="flex flex-wrap justify-between gap-2 py-3">
                      <span className="font-semibold">{name.replace(/_/g, ' ')}</span>
                      <div className="flex flex-wrap gap-3">
                        <span>{status || 'Status unreported'}</span>
                        {details?.uptime != null && <span>Uptime {details.uptime}</span>}
                        {response != null && <span>Response {response}</span>}
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
