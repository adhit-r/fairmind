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
  check: GateCheck['key']
  label: string
  relation: string
  confidence: number
  evidenceId: string | null
  evidenceClass: GateCheck['evidenceClass']
  /** This check's own cell, as the server derived it. */
  cell?: CellState
  stale?: true
  fails?: true
}

/** Per requirement of one framework, the cell of every system that confirmed it; `cells` follows `systems`. */
export interface FrameworkSystems {
  framework: { key: string; name: string }
  systems: Array<{ id: string; name: string; riskTier: SystemRecord['riskTier'] }>
  unconfirmed: number
  notInScope: number
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

export const useEstateGates = () => useOrgResource<EstateGate[]>(API_ENDPOINTS.aiGovernance.estateGates)
export const useFrameworkSystems = (frameworkKey: string | undefined) =>
  useOrgResource<FrameworkSystems>(frameworkKey ? API_ENDPOINTS.aiGovernance.frameworkSystems(frameworkKey) : null)
/** The 29 common controls and the crosswalk; `enabled` false keeps the request idle. */
export const useControls = (enabled = true) => useOrgResource<Controls>(enabled ? API_ENDPOINTS.packs.controls : null)
