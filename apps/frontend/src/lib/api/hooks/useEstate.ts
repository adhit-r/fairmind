'use client'

import type { CellState } from '@/components/ui/matrix'
import { API_ENDPOINTS } from '../endpoints'
import { useOrgResource } from './usePacks'
import type { GateCheck, ReleaseGate, SystemRecord } from './useSystemFile'

/** One system's release gate as GET /estate/gates returns it: no explain, path or check detail. */
export interface EstateGate {
  systemId: string
  verdict: ReleaseGate['verdict']
  confidence: number
  band: ReleaseGate['band']
  approvalStatus: string
  checks: Array<Omit<GateCheck, 'detail'> & { detail?: GateCheck['detail'] }>
}

export interface FrameworkCellCheck {
  /** A gate check key, or an evaluation id such as EV-DAT-01. */
  check: string
  label: string
  relation: string
  confidence: number
  evidenceId: string | null
  evidenceClass: GateCheck['evidenceClass']
  /** This check's own cell, as the server derived it; "not in gate" for a check the organisation left out of its gate. */
  cell?: CellState | 'not in gate'
  stale?: true
  fails?: true
}

/** Per requirement of one framework, the cell of every system that confirmed it; `cells` follows `systems`. */
export interface FrameworkSystems {
  framework: { key: string; name: string }
  systems: Array<{ id: string; name: string; riskTier: SystemRecord['riskTier'] }>
  unconfirmed: number
  notInScope: number
  /** Systems in scope because they inherit the plan's choice of this framework. */
  inherited?: number
  followedByPlan?: boolean
  requirements: Array<{ key: string; cells: Array<{ state: CellState; checks: FrameworkCellCheck[] } | null> }>
}

export interface CommonControl {
  id: string
  name: string
  objective: string | null
  workflows: Array<{ id: string; name: string; approver: string | null; scope: string | null }>
}

export interface Controls {
  controls: CommonControl[]
  crosswalk: Array<{ commonControl: string; key: string; relation: string }>
}

/** Per framework some system confirmed: how many systems, and its tracked requirements counted by weakest state. */
export interface EstateFrameworks {
  unconfirmed: number
  /** Frameworks the organisation chose in its plan; systems that have not confirmed their own inherit them. */
  plan?: string[]
  frameworks: Array<{
    key: string
    systems: number
    tracked: number
    states: Partial<Record<CellState | 'none', number>>
    /** plan: chosen in the plan; system: only confirmed on systems. */
    source?: 'plan' | 'system'
    inherited?: number
    confirmed?: number
  }>
}

export const useEstateFrameworks = () => useOrgResource<EstateFrameworks>(API_ENDPOINTS.aiGovernance.estateFrameworks)
/** Failed runs per week, oldest first; weekStart is the Monday. */
export type FailedRunsWeek = { weekStart: string; failed: number }
export const useEstateFailedRuns = () => useOrgResource<FailedRunsWeek[]>(API_ENDPOINTS.aiGovernance.estateFailedRuns)
export const useEstateGates = () => useOrgResource<EstateGate[]>(API_ENDPOINTS.aiGovernance.estateGates)
export const useFrameworkSystems = (frameworkKey: string | undefined) =>
  useOrgResource<FrameworkSystems>(frameworkKey ? API_ENDPOINTS.aiGovernance.frameworkSystems(frameworkKey) : null)
/** The 29 common controls and the crosswalk; `enabled` false keeps the request idle. */
export const useControls = (enabled = true) => useOrgResource<Controls>(enabled ? API_ENDPOINTS.packs.controls : null)
