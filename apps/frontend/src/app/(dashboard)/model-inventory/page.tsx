'use client'

import { useMemo, useState } from 'react'
import {
  IconAlertHexagon,
  IconAlertTriangle,
  IconCircleCheck,
  IconDatabase,
  IconFilterSearch,
  IconLoader2,
  IconSearch,
  IconShieldOff,
} from '@tabler/icons-react'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { useModelInventory, type AISystem } from '@/lib/api/hooks/useModelInventory'
import { LifecycleStepper } from './components/LifecycleStepper'
import { SystemDetailDrawer } from './components/SystemDetailDrawer'

const RISK_TIER_COLORS: Record<string, string> = {
  critical: 'border-red-600 bg-red-100 text-red-800',
  high: 'border-orange-500 bg-orange-100 text-orange-800',
  medium: 'border-amber-500 bg-amber-100 text-amber-800',
  low: 'border-emerald-500 bg-emerald-100 text-emerald-800',
}

function SystemRow({ system, onClick }: { system: AISystem; onClick: () => void }) {
  const ls = system.lifecycleSummary

  const recIcon =
    ls.releaseRecommendation === 'Go' ? <IconCircleCheck className="h-4 w-4 text-emerald-600" /> :
    ls.releaseRecommendation === 'Conditional Go' ? <IconAlertTriangle className="h-4 w-4 text-amber-600" /> :
    <IconShieldOff className="h-4 w-4 text-red-600" />

  const recColor =
    ls.releaseRecommendation === 'Go' ? 'text-emerald-700' :
    ls.releaseRecommendation === 'Conditional Go' ? 'text-amber-700' :
    'text-red-700'

  return (
    <button
      type="button"
      onClick={onClick}
      className="group w-full rounded-xl border-2 border-black bg-white p-4 text-left shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all hover:shadow-[5px_5px_0px_0px_rgba(0,0,0,1)] hover:-translate-x-0.5 hover:-translate-y-0.5"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:gap-5">
        {/* Name + badges */}
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-base font-black">{system.name}</p>
            <Badge className={`border-2 px-2 py-0.5 text-[10px] font-black uppercase ${RISK_TIER_COLORS[system.riskTier] ?? 'border-black bg-white text-black'}`}>
              {system.riskTier} risk
            </Badge>
            {ls.criticalBlockers > 0 && (
              <Badge className="border-2 border-red-600 bg-red-100 px-2 py-0.5 text-[10px] font-black uppercase text-red-800">
                <IconAlertHexagon className="mr-1 h-2.5 w-2.5" />
                {ls.criticalBlockers} blocker{ls.criticalBlockers !== 1 ? 's' : ''}
              </Badge>
            )}
          </div>
          {system.owner && (
            <p className="text-xs text-muted-foreground">Owner: {system.owner}</p>
          )}
          <LifecycleStepper currentStage={system.lifecycleStage} readiness={system.readiness} compact />
        </div>

        {/* Readiness + recommendation */}
        <div className="flex shrink-0 items-center gap-4 lg:flex-col lg:items-end lg:gap-2">
          <div className="flex items-center gap-1.5">
            {recIcon}
            <span className={`text-xs font-black uppercase ${recColor}`}>
              {ls.releaseRecommendation}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-muted-foreground">Readiness</span>
            <span className="text-sm font-black">{system.readiness}%</span>
          </div>
          <div className="hidden w-24 lg:block">
            <Progress value={system.readiness} className="h-2 border border-black" />
          </div>
        </div>

        {/* Risk counts */}
        <div className="flex items-center gap-3 lg:flex-col lg:items-end lg:gap-1">
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase text-muted-foreground">Open risks</p>
            <p className={`text-lg font-black ${ls.openRisks > 0 ? 'text-red-700' : ''}`}>{ls.openRisks}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase text-muted-foreground">Remediation</p>
            <p className={`text-lg font-black ${ls.activeRemediation > 0 ? 'text-amber-700' : ''}`}>{ls.activeRemediation}</p>
          </div>
        </div>
      </div>
    </button>
  )
}

export default function ModelInventoryPage() {
  const { systems, loading, error, refreshSystems, fetchSystemRisks, fetchSystemApprovals } = useModelInventory()

  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState<string>('all')
  const [stageFilter, setStageFilter] = useState<string>('all')
  const [selectedSystem, setSelectedSystem] = useState<AISystem | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const filteredSystems = useMemo(() => {
    let result = systems
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        (s) => s.name.toLowerCase().includes(q) || (s.owner ?? '').toLowerCase().includes(q)
      )
    }
    if (riskFilter !== 'all') {
      result = result.filter((s) => s.riskTier === riskFilter)
    }
    if (stageFilter !== 'all') {
      result = result.filter((s) => s.lifecycleStage === stageFilter)
    }
    return result
  }, [systems, search, riskFilter, stageFilter])

  const stats = useMemo(() => {
    const total = systems.length
    const criticalBlockers = systems.filter((s) => s.lifecycleSummary.criticalBlockers > 0).length
    const approved = systems.filter((s) => s.lifecycleSummary.approvalStatus === 'approved').length
    const avgReadiness = total > 0
      ? Math.round(systems.reduce((sum, s) => sum + s.readiness, 0) / total)
      : 0
    return { total, criticalBlockers, approved, avgReadiness }
  }, [systems])

  const openDrawer = (system: AISystem) => {
    setSelectedSystem(system)
    setDrawerOpen(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-4 border-black bg-gradient-to-br from-[#f0f4ff] via-white to-[#fff4de] p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                <IconDatabase className="mr-2 h-4 w-4" />
                Model Inventory
              </Badge>
            </div>
            <h1 className="text-3xl font-black uppercase tracking-tight">
              Governance Registry
            </h1>
            <p className="max-w-2xl text-sm text-muted-foreground">
              Lifecycle-aware registry of all registered AI systems with risk scores, governance states, and decision logs.
            </p>
          </div>
          <Button
            variant="neutral"
            className="border-2 border-black font-bold"
            onClick={() => void refreshSystems()}
            disabled={loading}
          >
            Refresh
          </Button>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-4">
        <Card className="border-2 border-black p-4 shadow-brutal">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Total systems</p>
          <p className="mt-1 text-3xl font-black">{stats.total}</p>
        </Card>
        <Card className="border-2 border-black p-4 shadow-brutal">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Approved</p>
          <p className="mt-1 text-3xl font-black text-emerald-700">{stats.approved}</p>
        </Card>
        <Card className={`border-2 border-black p-4 shadow-brutal ${stats.criticalBlockers > 0 ? 'bg-red-50' : ''}`}>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">With blockers</p>
          <p className={`mt-1 text-3xl font-black ${stats.criticalBlockers > 0 ? 'text-red-700' : ''}`}>{stats.criticalBlockers}</p>
        </Card>
        <Card className="border-2 border-black p-4 shadow-brutal">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Avg readiness</p>
          <p className="mt-1 text-3xl font-black">{stats.avgReadiness}%</p>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1">
          <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border-2 border-black pl-9 font-medium"
            placeholder="Search by name or owner..."
          />
        </div>
        <Select value={riskFilter} onValueChange={setRiskFilter}>
          <SelectTrigger className="w-40 border-2 border-black font-bold">
            <IconFilterSearch className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Risk tier" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All risk tiers</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
        <Select value={stageFilter} onValueChange={setStageFilter}>
          <SelectTrigger className="w-44 border-2 border-black font-bold">
            <SelectValue placeholder="Lifecycle stage" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All stages</SelectItem>
            <SelectItem value="onboard">Registered</SelectItem>
            <SelectItem value="assess">Assessed</SelectItem>
            <SelectItem value="govern">Evidenced</SelectItem>
            <SelectItem value="remediate">Remediating</SelectItem>
            <SelectItem value="operate">Approved</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* System list */}
      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-black bg-slate-50 py-16 text-center">
          <IconLoader2 className="h-8 w-8 animate-spin" />
          <p className="font-bold">Loading model inventory...</p>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-3xl border-2 border-red-600 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <IconAlertTriangle className="mt-0.5 h-5 w-5 text-red-700" />
            <div>
              <p className="font-bold text-red-800">Could not load model inventory</p>
              <p className="text-sm text-red-700">{error.message}</p>
              <Button
                variant="neutral"
                className="mt-3 border-2 border-red-700 font-bold text-red-700"
                onClick={() => void refreshSystems()}
              >
                Retry
              </Button>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && systems.length === 0 && (
        <div className="rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-16 text-center">
          <IconDatabase className="mx-auto h-12 w-12 opacity-50" />
          <h3 className="mt-4 text-xl font-black">No AI systems registered</h3>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
            Register your first AI system via the Onboard flow to begin tracking its governance lifecycle.
          </p>
        </div>
      )}

      {!loading && !error && systems.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase text-muted-foreground">
            {filteredSystems.length} system{filteredSystems.length !== 1 ? 's' : ''}
            {systems.length !== filteredSystems.length && ` (${systems.length} total)`}
          </p>
          {filteredSystems.length === 0 ? (
            <div className="rounded-3xl border-2 border-dashed border-black bg-slate-50 px-6 py-10 text-center">
              <p className="font-bold text-muted-foreground">No systems match your filters.</p>
              <Button
                variant="neutral"
                size="sm"
                className="mt-3 border-2 border-black font-bold"
                onClick={() => { setSearch(''); setRiskFilter('all'); setStageFilter('all') }}
              >
                Clear filters
              </Button>
            </div>
          ) : (
            filteredSystems.map((system) => (
              <SystemRow key={system.id} system={system} onClick={() => openDrawer(system)} />
            ))
          )}
        </div>
      )}

      {/* System detail drawer */}
      <SystemDetailDrawer
        system={selectedSystem}
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setSelectedSystem(null) }}
        onFetchRisks={fetchSystemRisks}
        onFetchApprovals={fetchSystemApprovals}
      />
    </div>
  )
}
