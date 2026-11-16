'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { IconBuilding, IconExternalLink, IconPlus, IconRefresh } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useOrg } from '@/context/OrgContext'
import { useSystemContext } from '@/components/workflow/SystemContext'
import { cn } from '@/lib/utils'

/**
 * Routes whose content is scoped to one AI system. The ScopeBar is shown only
 * here (not on the systems list, registration wizard, admin, settings, policies
 * or monitoring).
 */
export function isSystemScopedRoute(pathname: string | null | undefined): boolean {
  if (!pathname) return false
  const prefixes = ['/frameworks', '/evaluations', '/assurance/evaluations', '/evidence', '/findings', '/remediation', '/reports']
  if (prefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))) return true
  const systemDetail = /^\/systems\/([^/]+)/.exec(pathname)
  return Boolean(systemDetail && systemDetail[1] !== 'new')
}

function systemIdFromPath(pathname: string | null | undefined): string | null {
  const match = pathname ? /^\/systems\/([^/]+)/.exec(pathname) : null
  return match && match[1] !== 'new' ? decodeURIComponent(match[1]) : null
}

export interface ScopeBarProps {
  className?: string
}

/**
 * Compact organization + AI system scope strip. Replaces the old
 * OrgSwitcher + SystemContextBar stack. Never shows a fabricated system: when
 * systems cannot be loaded or none exist it says so and offers a next step.
 */
export function ScopeBar({ className }: ScopeBarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { organizations, selectedOrg, selectOrg, isLoading: orgLoading, error: orgError, refreshOrgs } = useOrg()
  const { systems, activeSystem, setSelectedSystemId, loading: systemsLoading, systemsError, refreshSystems } = useSystemContext()
  const orgSelectId = React.useId()
  const systemSelectId = React.useId()
  const routeSystemId = systemIdFromPath(pathname)

  // On /systems/[id] the URL is the source of truth for the selected system.
  React.useEffect(() => {
    if (routeSystemId && routeSystemId !== activeSystem?.id && systems.some((system) => system.id === routeSystemId)) {
      setSelectedSystemId(routeSystemId)
    }
  }, [routeSystemId, activeSystem?.id, systems, setSelectedSystemId])

  const handleSystemChange = (systemId: string) => {
    setSelectedSystemId(systemId)
    if (routeSystemId) router.push(`/systems/${encodeURIComponent(systemId)}`)
  }

  const orgControl = (() => {
    if (orgLoading) return <span className="text-sm text-muted-foreground">Loading organizations</span>
    if (orgError) {
      return (
        <span className="flex items-center gap-2 text-sm text-destructive-strong">
          Could not load organizations
          <Button type="button" variant="ghost" size="sm" onClick={() => void refreshOrgs()}>
            <IconRefresh aria-hidden="true" />
            Retry
          </Button>
        </span>
      )
    }
    if (organizations.length === 0) return <span className="text-sm text-muted-foreground">No organization assigned</span>
    if (organizations.length === 1) {
      return (
        <span className="flex min-h-11 items-center gap-2 text-sm font-medium text-foreground">
          <IconBuilding className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          {selectedOrg?.name}
        </span>
      )
    }
    return (
      <Select value={selectedOrg?.id ?? ''} onValueChange={selectOrg}>
        <SelectTrigger id={orgSelectId} className="min-w-[180px]">
          <SelectValue placeholder="Select organization" />
        </SelectTrigger>
        <SelectContent>
          {organizations.map((org) => (
            <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  })()

  const systemControl = (() => {
    if (systemsLoading) return <span className="text-sm text-muted-foreground">Loading AI systems</span>
    if (systemsError) {
      return (
        <span className="flex flex-wrap items-center gap-2 text-sm text-destructive-strong">
          Could not load AI systems
          <Button type="button" variant="ghost" size="sm" onClick={() => void refreshSystems()}>
            <IconRefresh aria-hidden="true" />
            Retry
          </Button>
        </span>
      )
    }
    if (systems.length === 0) {
      return (
        <span className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          No AI systems registered yet
          <Button asChild variant="outline" size="sm">
            <Link href="/systems/new">
              <IconPlus aria-hidden="true" />
              Register AI system
            </Link>
          </Button>
        </span>
      )
    }
    return (
      <Select value={activeSystem?.id ?? ''} onValueChange={handleSystemChange}>
        <SelectTrigger id={systemSelectId} className="min-w-[220px]">
          <SelectValue placeholder="Select AI system" />
        </SelectTrigger>
        <SelectContent>
          {systems.map((system) => (
            <SelectItem key={system.id} value={system.id}>{system.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  })()

  const showOrgLabel = !orgLoading && !orgError && organizations.length > 1
  const showSystemLabel = !systemsLoading && !systemsError && systems.length > 0

  return (
    <section
      aria-label="Scope: organization and AI system"
      className={cn('mb-5 flex flex-col gap-3 rounded-lg border border-border bg-card px-3 py-2 sm:flex-row sm:flex-wrap sm:items-end sm:gap-x-6', className)}
    >
      <div className="space-y-1">
        {showOrgLabel ? (
          <Label htmlFor={orgSelectId} className="text-xs text-muted-foreground">Organization</Label>
        ) : (
          <p className="text-xs font-medium text-muted-foreground">Organization</p>
        )}
        {orgControl}
      </div>
      <div className="space-y-1">
        {showSystemLabel ? (
          <Label htmlFor={systemSelectId} className="text-xs text-muted-foreground">AI system</Label>
        ) : (
          <p className="text-xs font-medium text-muted-foreground">AI system</p>
        )}
        {systemControl}
      </div>
      {activeSystem && (
        <Button asChild variant="ghost" size="sm" className="sm:ml-auto">
          <Link href={`/systems/${encodeURIComponent(activeSystem.id)}`}>
            View system
            <IconExternalLink aria-hidden="true" />
          </Link>
        </Button>
      )}
    </section>
  )
}
