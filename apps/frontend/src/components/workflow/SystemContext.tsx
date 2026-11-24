"use client"

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { IconBuildingSkyscraper, IconPlus, IconRouteAltLeft, IconShieldCheck } from "@tabler/icons-react"

import { apiClient, type ApiResponse } from "@/lib/api/api-client"
import { API_ENDPOINTS } from "@/lib/api/endpoints"
import { withOrg } from "@/lib/api/hooks/usePacks"
import { useOrg } from "@/context/OrgContext"

export interface AISystemSummary {
  id: string
  name: string
  owner: string
  riskTier: "low" | "medium" | "high" | "critical"
  /** Null when the backend has not reported readiness for this system. */
  readiness: number | null
  stage: "onboard" | "assess" | "govern" | "remediate" | "operate" | "retired"
  workspaceId?: string
  metadata?: Record<string, unknown>
  /** When the system was registered; absent on the empty-state placeholder. */
  createdAt?: string
}

interface WorkspaceRecord {
  id: string
  name: string
  owner?: string | null
}

interface AISystemRecord {
  id: string
  workspaceId: string
  name: string
  owner?: string | null
  riskTier: AISystemSummary["riskTier"]
  lifecycleStage: AISystemSummary["stage"]
  readiness?: number
  lifecycleSummary?: Partial<SelectedSystemStatus> & {
    stage?: AISystemSummary["stage"]
    readiness?: number
  }
  metadata?: Record<string, unknown>
  createdAt?: string
}

interface SelectedSystemStatus {
  readiness: number | null
  stage: AISystemSummary["stage"]
  criticalBlockers: number
  failedControls: number
  missingEvidence: number
  openRisks: number
  activeRemediation: number
}

// Empty state, not a system: shown until the org registers its first AI system.
// Consumers detect it through metadata.source === "fallback".
const NO_SYSTEM: AISystemSummary = {
  id: "",
  name: "No system registered",
  owner: "unassigned",
  riskTier: "low",
  readiness: null,
  stage: "onboard",
  workspaceId: "",
  metadata: { source: "fallback" },
}

type SystemContextValue = {
  systems: AISystemSummary[]
  selectedSystem: AISystemSummary
  selectedSystemStatus: SelectedSystemStatus
  setSelectedSystemId: (systemId: string) => void
  loading: boolean
  /** Why the systems request failed; null when it succeeded, including when the org has no systems. */
  error: string | null
  refreshSystems: () => Promise<void>
  createWorkspaceAndSystem: (params: {
    workspaceName: string
    workspaceOwner: string
    systemName: string
    systemOwner: string
    riskTier: AISystemSummary["riskTier"]
    stage: AISystemSummary["stage"]
    kind?: string
    systemVersion?: string
    businessLine?: string
    complianceFrameworks?: string[]
    /** Client-chosen ids: replaying a create with the same ids returns the rows it made instead of new ones. */
    ids?: { workspace: string; system: string }
  }) => Promise<AISystemSummary>
}

const SystemContext = createContext<SystemContextValue | null>(null)

function getStoredSystemId() {
  if (typeof window === "undefined") {
    return null
  }
  return window.localStorage.getItem("fairmind:selected-ai-system")
}

/** A `?system=<id>` in the URL wins over the remembered selection, so links are shareable. */
function getUrlSystemId() {
  if (typeof window === "undefined") return null
  return new URLSearchParams(window.location.search).get("system")
}

export function chooseSelectedSystemId(
  systemIds: string[],
  currentId: string,
  storedId: string | null,
) {
  if (storedId && systemIds.includes(storedId)) return storedId
  if (systemIds.includes(currentId)) return currentId
  return systemIds[0]
}

function emptyDerivedStatus(system: AISystemSummary): SelectedSystemStatus {
  return {
    readiness: null,
    stage: system.stage,
    criticalBlockers: 0,
    failedControls: 0,
    missingEvidence: 0,
    openRisks: 0,
    activeRemediation: 0,
  }
}

function normalizeSystem(record: AISystemRecord): AISystemSummary {
  const lifecycleSummary = record.lifecycleSummary || {}
  const stage = lifecycleSummary.stage || record.lifecycleStage
  // The backend is the only source of readiness; a record without one is unknown, not 0.
  const readiness = lifecycleSummary.readiness ?? record.readiness ?? null
  return {
    id: record.id,
    name: record.name,
    owner: record.owner || "unassigned",
    riskTier: record.riskTier,
    readiness,
    stage,
    workspaceId: record.workspaceId,
    createdAt: record.createdAt,
    metadata: {
      ...(record.metadata || {}),
      lifecycleSummary,
    },
  }
}

interface SystemRegister {
  orgId?: string
  systems: AISystemSummary[]
  loading: boolean
  error: string | null
}

const EMPTY_REGISTER: SystemRegister = { systems: [], loading: true, error: null }

export function SystemContextProvider({ children }: { children: React.ReactNode }) {
  const { selectedOrg, isLoading: orgLoading, error: orgError, refreshOrgs } = useOrg()
  const orgId = selectedOrg?.id
  const [register, setRegister] = useState<SystemRegister>(EMPTY_REGISTER)
  const { systems, loading, error } = register.orgId === orgId ? register : EMPTY_REGISTER
  const [selectedSystemId, setSelectedSystemId] = useState<string>("")
  const request = useRef(0)

  const refreshSystems = useCallback(async () => {
    if (!orgId) return
    const version = ++request.current
    setRegister((current) => ({ ...(current.orgId === orgId ? current : EMPTY_REGISTER), orgId, loading: true, error: null }))
    try {
      const response = await apiClient.get<AISystemRecord[]>(withOrg(API_ENDPOINTS.aiGovernance.systems, orgId))
      if (version !== request.current) return
      if (!response.success || !Array.isArray(response.data)) {
        throw new Error(response.error || "Failed to load AI systems")
      }
      const nextSystems = response.data.map(normalizeSystem)
      setRegister({ orgId, systems: nextSystems, loading: false, error: null })
      setSelectedSystemId((current) => chooseSelectedSystemId(
        nextSystems.map((system) => system.id), current, getUrlSystemId() ?? getStoredSystemId(),
      ) ?? "")
    } catch (err) {
      if (version !== request.current) return
      setRegister({ orgId, systems: [], loading: false, error: err instanceof Error ? err.message : "Failed to load AI systems" })
      setSelectedSystemId("")
    }
  }, [orgId])

  useEffect(() => {
    void refreshSystems()
    return () => { request.current += 1 }
  }, [refreshSystems])

  const setAndPersist = useCallback((systemId: string) => {
    setSelectedSystemId(systemId)
    if (typeof window !== "undefined") {
      window.localStorage.setItem("fairmind:selected-ai-system", systemId)
    }
  }, [])

  const createWorkspaceAndSystem = async (params: {
    workspaceName: string
    workspaceOwner: string
    systemName: string
    systemOwner: string
    riskTier: AISystemSummary["riskTier"]
    stage: AISystemSummary["stage"]
    kind?: string
    systemVersion?: string
    businessLine?: string
    complianceFrameworks?: string[]
    ids?: { workspace: string; system: string }
  }) => {
    if (!orgId) throw new Error("Choose an organisation before registering an AI system.")
    const workspaceResponse: ApiResponse<WorkspaceRecord> = await apiClient.post(
      withOrg(API_ENDPOINTS.aiGovernance.workspaces, orgId),
      {
        ...(params.ids && { id: params.ids.workspace }),
        name: params.workspaceName,
        owner: params.workspaceOwner,
      }
    )

    if (!workspaceResponse.success || !workspaceResponse.data) {
      throw new Error(workspaceResponse.error || "Failed to create workspace")
    }

    const systemResponse: ApiResponse<AISystemRecord> = await apiClient.post(
      withOrg(API_ENDPOINTS.aiGovernance.systems, orgId),
      {
        ...(params.ids && { id: params.ids.system }),
        workspace_id: workspaceResponse.data.id,
        name: params.systemName,
        owner: params.systemOwner,
        risk_tier: params.riskTier,
        lifecycle_stage: params.stage,
        metadata: {
          created_from: "onboard",
          workspace_name: params.workspaceName,
          ...(params.kind && { asset_kind: params.kind }),
          ...(params.systemVersion && { system_version: params.systemVersion }),
          ...(params.businessLine && { business_line: params.businessLine }),
          ...(params.complianceFrameworks && { compliance_frameworks: params.complianceFrameworks }),
        },
      }
    )

    if (!systemResponse.success || !systemResponse.data) {
      throw new Error(systemResponse.error || "Failed to create AI system")
    }

    const nextSystem = normalizeSystem(systemResponse.data)
    setRegister((current) => current.orgId === orgId
      ? { ...current, systems: [nextSystem, ...current.systems.filter((item) => item.id !== nextSystem.id)] }
      : current)
    setAndPersist(nextSystem.id)
    return nextSystem
  }

  const selectedSystem = useMemo(() => {
    return systems.find((system) => system.id === selectedSystemId) || systems[0] || NO_SYSTEM
  }, [selectedSystemId, systems])

  const selectedSystemStatus = useMemo<SelectedSystemStatus>(() => {
    if (!selectedSystem || selectedSystem.metadata?.source === "fallback") {
      return emptyDerivedStatus(selectedSystem || NO_SYSTEM)
    }

    const lifecycleSummary = (selectedSystem.metadata?.lifecycleSummary || {}) as Partial<SelectedSystemStatus>
    return {
      readiness: typeof lifecycleSummary.readiness === "number" ? lifecycleSummary.readiness : selectedSystem.readiness,
      stage: (lifecycleSummary.stage as AISystemSummary["stage"]) || selectedSystem.stage,
      criticalBlockers: lifecycleSummary.criticalBlockers || 0,
      failedControls: lifecycleSummary.failedControls || 0,
      missingEvidence: lifecycleSummary.missingEvidence || 0,
      openRisks: lifecycleSummary.openRisks || 0,
      activeRemediation: lifecycleSummary.activeRemediation || 0,
    }
  }, [selectedSystem])

  const selectedSystemWithStatus = useMemo(
    () => ({
      ...selectedSystem,
      readiness: selectedSystemStatus.readiness,
      stage: selectedSystemStatus.stage,
    }),
    [selectedSystem, selectedSystemStatus.readiness, selectedSystemStatus.stage]
  )

  return (
    <SystemContext.Provider
      value={{
        systems,
        selectedSystem: selectedSystemWithStatus,
        selectedSystemStatus,
        setSelectedSystemId: setAndPersist,
        loading: orgLoading || Boolean(orgId && loading),
        error: orgError || (!orgId && !orgLoading ? "Choose an organisation to load its AI systems." : error),
        refreshSystems: orgId && !orgError ? refreshSystems : refreshOrgs,
        createWorkspaceAndSystem,
      }}
    >
      {children}
    </SystemContext.Provider>
  )
}

export function useSystemContext() {
  const context = useContext(SystemContext)
  if (!context) {
    throw new Error("useSystemContext must be used within SystemContextProvider")
  }
  return context
}

function riskTierClassName(riskTier: AISystemSummary["riskTier"]) {
  if (riskTier === "critical" || riskTier === "high") return "bg-red-100 text-red-800 border-red-500"
  if (riskTier === "medium") return "bg-amber-100 text-amber-800 border-amber-500"
  return "bg-emerald-100 text-emerald-800 border-emerald-500"
}

export function SystemContextBar() {
  const { systems, selectedSystem, selectedSystemStatus, setSelectedSystemId, loading } = useSystemContext()

  if (selectedSystem.metadata?.source === "fallback") {
    return null
  }

  const realSystems = systems.filter((system) => system.metadata?.source !== "fallback")

  return (
    <section aria-label="Selected AI system context" className="mb-6 border border-[var(--fm-line)] bg-white p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3">
          <div className="bg-[var(--fm-ink)] p-3 text-white rounded-[14px] shadow-[var(--fm-shadow)]">
            <IconBuildingSkyscraper className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Current AI System
            </p>
            <h2 className="text-xl font-semibold">{selectedSystem.name}</h2>
            <p className="text-sm text-muted-foreground">{selectedSystem.owner}</p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-4 lg:min-w-[720px]">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase text-muted-foreground">System Scope</p>
            {realSystems.length > 0 ? (
              <Select onValueChange={setSelectedSystemId} value={selectedSystem.id}>
                <SelectTrigger aria-label="System scope" className="border border-[var(--fm-line)] bg-white font-bold">
                  <SelectValue placeholder={loading ? "Loading systems..." : "Select system"} />
                </SelectTrigger>
                <SelectContent>
                  {realSystems.map((system) => (
                    <SelectItem key={system.id} value={system.id}>
                      {system.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Button asChild variant="neutral" className="w-full border border-[var(--fm-line)] font-bold">
                <a href="/onboard">
                  <IconPlus className="mr-2 h-4 w-4" />
                  Create system
                </a>
              </Button>
            )}
          </div>

          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase text-muted-foreground">Risk Tier</p>
            <Badge className={`border-2 px-3 py-2 font-semibold ${riskTierClassName(selectedSystem.riskTier)}`}>
              <IconShieldCheck className="mr-2 h-4 w-4" />
              {selectedSystem.riskTier}
            </Badge>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase text-muted-foreground">Readiness</p>
            <div className="border border-[var(--fm-line)] bg-white px-3 py-2 font-semibold">
              {selectedSystemStatus.readiness === null ? "Unknown" : `${selectedSystemStatus.readiness}%`}
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase text-muted-foreground">Lifecycle Stage</p>
            <Badge className="border border-[var(--fm-line)] bg-[var(--fm-ink)] px-3 py-2 font-semibold text-white">
              <IconRouteAltLeft className="mr-2 h-4 w-4 text-[var(--fm-brand)]" />
              {selectedSystemStatus.stage}
            </Badge>
          </div>
        </div>
      </div>
    </section>
  )
}
