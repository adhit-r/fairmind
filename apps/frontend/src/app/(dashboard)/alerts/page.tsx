'use client'

import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react'
import { when } from '@/components/packs/parts'
import { useOrgId } from '@/lib/api/hooks/useOrgId'
import { usePolicyResource, type PolicyAlert } from '@/lib/api/hooks/usePolicies'

export default function AlertsPage() {
  const orgId = useOrgId()
  const { data, loading, error, reload } = usePolicyResource<PolicyAlert[]>(orgId, '/alerts')
  const alerts = (data ?? []).filter((a) => a.status === 'open')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[30px] font-semibold tracking-[-.03em]">Alerts</h1>
          <p className="text-muted-foreground mt-1">Published policy rules that are failing on a system</p>
        </div>
        <Button onClick={() => void reload()}>
          <IconRefresh className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert className="border border-[var(--fm-line)]">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertTitle>Alerts Unavailable</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card className="p-6 fm-card">
        {!orgId ? (
          <p className="text-muted-foreground">Select an organisation to see its alerts.</p>
        ) : loading ? (
          <p>Loading alerts...</p>
        ) : alerts.length === 0 ? (
          <p className="text-muted-foreground">No open alerts.</p>
        ) : (
          <div className="space-y-3">
            {alerts.map((a) => (
              <div key={a.id} className="rounded-[10px] border border-[var(--fm-line)] p-3">
                <div className="font-semibold text-sm">{a.severity} - {a.enforcement}</div>
                <div>{a.systemName}: {a.ruleTitle}</div>
                <div className="text-sm text-muted-foreground">{a.detail}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Failing since {when(a.openedAt)} ·{' '}
                  <Link href={`/policies/${a.policyId}`} className="font-semibold hover:underline">{a.policyName}</Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
