"use client"

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"
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

export interface AISystemSummary {
  id: string
  name: string
  owner: string
  riskTier: "low" | "medium" | "high" | "critical"
  readiness: number
  stage: "onboard" | "assess" | "govern" | "remediate" | "operate"
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
  readiness: number
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
  readiness: 0,
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
    systemType?: string
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
    readiness: 0,
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
  // The backend is the only source of readiness; a record without one reads 0.
  const readiness = lifecycleSummary.readiness ?? record.readiness ?? 0
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

export function SystemContextProvider({ children }: { children: React.ReactNode }) {
  const [systems, setSystems] = useState<AISystemSummary[]>([])
  const [selectedSystemId, setSelectedSystemId] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSystemStatus, setSelectedSystemStatus] = useState<SelectedSystemStatus>(
    emptyDerivedStatus(NO_SYSTEM)
  )

  const refreshSystems = async () => {
    setLoading(true)
    setError(null)
    try {
      const response: ApiResponse<AISystemRecord[]> = await apiClient.get(API_ENDPOINTS.aiGovernance.systems)
      if (!response.success || !response.data) {
        throw new Error(response.error || "Failed to load AI systems")
      }
      if (response.data.length > 0) {
        const nextSystems = response.data.map(normalizeSystem)
        setSystems(nextSystems)
        setSelectedSystemId((currentId) => {
          return chooseSelectedSystemId(
            nextSystems.map((system) => system.id),
            currentId,
            getUrlSystemId() ?? getStoredSystemId(),
          )
        })
      } else {
        setSystems([])
        setSelectedSystemId("")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load AI systems")
      setSystems([])
      setSelectedSystemId("")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refreshSystems()
  }, [])

  const setAndPersist = (systemId: string) => {
    setSelectedSystemId(systemId)
    if (typeof window !== "undefined") {
      window.localStorage.setItem("fairmind:selected-ai-system", systemId)
    }
  }

  const createWorkspaceAndSystem = async (params: {
    workspaceName: string
    workspaceOwner: string
    systemName: string
    systemOwner: string
    riskTier: AISystemSummary["riskTier"]
    stage: AISystemSummary["stage"]
    systemType?: string
    systemVersion?: string
    businessLine?: string
    complianceFrameworks?: string[]
    ids?: { workspace: string; system: string }
  }) => {
    const workspaceResponse: ApiResponse<WorkspaceRecord> = await apiClient.post(
      API_ENDPOINTS.aiGovernance.workspaces,
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
      API_ENDPOINTS.aiGovernance.systems,
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
          ...(params.systemType && { system_type: params.systemType }),
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
    setSystems((current) => {
      const next = [nextSystem, ...current.filter((item) => item.id !== nextSystem.id)]
      return next
    })
    setAndPersist(nextSystem.id)
    return nextSystem
  }

  const selectedSystem = useMemo(() => {
    return systems.find((system) => system.id === selectedSystemId) || systems[0] || NO_SYSTEM
  }, [selectedSystemId, systems])

  useEffect(() => {
    if (!selectedSystem || selectedSystem.metadata?.source === "fallback") {
      setSelectedSystemStatus(emptyDerivedStatus(selectedSystem || NO_SYSTEM))
      return
    }

    const lifecycleSummary = (selectedSystem.metadata?.lifecycleSummary || {}) as Partial<SelectedSystemStatus>
    setSelectedSystemStatus({
      readiness: typeof lifecycleSummary.readiness === "number" ? lifecycleSummary.readiness : selectedSystem.readiness,
      stage: (lifecycleSummary.stage as AISystemSummary["stage"]) || selectedSystem.stage,
      criticalBlockers: lifecycleSummary.criticalBlockers || 0,
      failedControls: lifecycleSummary.failedControls || 0,
      missingEvidence: lifecycleSummary.missingEvidence || 0,
      openRisks: lifecycleSummary.openRisks || 0,
      activeRemediation: lifecycleSummary.activeRemediation || 0,
    })
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
        loading,
        error,
        refreshSystems,
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
              {selectedSystemStatus.readiness}%
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
