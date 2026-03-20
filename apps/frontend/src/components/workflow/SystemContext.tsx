"use client"

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
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
}

interface RiskDashboardSummary {
  total: number
  open: number
  automated: number
  bySeverity: Record<"low" | "medium" | "high" | "critical", number>
}

interface RiskDashboardResponse {
  risks: Array<Record<string, unknown>>
  summary: RiskDashboardSummary
}

interface EvidenceSummaryResponse {
  systemId: string
  totalEvidence: number
  linkedEvidence: number
  averageConfidence: number
  highConfidenceEvidence: number
  evidenceTypes: Array<{ type: string; count: number }>
  metadataSources: Array<{ source: string; count: number }>
  workflowState: string
  decisionReadiness: string
  missingSignals: string[]
  recommendedNextStep: string
}

interface RemediationSummaryResponse {
  systemId: string
  total: number
  active: number
  completed: number
  retestRequiredTasks: number
  linkedRiskReferences: number
  byStatus: Record<string, number>
  byPriority: Record<string, number>
}

interface RemediationListResponse {
  tasks: Array<Record<string, unknown>>
  summary: RemediationSummaryResponse
}

interface ApprovalRequestRecord {
  id: string
  status: "pending" | "approved" | "rejected"
}

interface ApprovalStateResponse {
  systemId: string
  request: ApprovalRequestRecord | null
  decisions: Array<Record<string, unknown>>
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

const FALLBACK_SYSTEMS: AISystemSummary[] = [
  {
    id: "acme-pricing-lab",
    name: "Acme Pricing Lab",
    owner: "ml-platform@acme.ai",
    riskTier: "medium",
    readiness: 18,
    stage: "onboard",
    workspaceId: "fallback-workspace",
    metadata: { source: "fallback" },
  },
]

type SystemContextValue = {
  systems: AISystemSummary[]
  selectedSystem: AISystemSummary
  selectedSystemStatus: SelectedSystemStatus
  setSelectedSystemId: (systemId: string) => void
  loading: boolean
  refreshSystems: () => Promise<void>
  createWorkspaceAndSystem: (params: {
    workspaceName: string
    workspaceOwner: string
    systemName: string
    systemOwner: string
    riskTier: AISystemSummary["riskTier"]
    stage: AISystemSummary["stage"]
  }) => Promise<AISystemSummary>
}

const SystemContext = createContext<SystemContextValue | null>(null)

function getStoredSystemId(fallbackId: string) {
  if (typeof window === "undefined") {
    return fallbackId
  }
  return window.localStorage.getItem("fairmind:selected-ai-system") || fallbackId
}

function estimateReadiness(stage: AISystemSummary["stage"]) {
  if (stage === "onboard") return 20
  if (stage === "assess") return 45
  if (stage === "govern") return 65
  if (stage === "remediate") return 78
  return 88
}

function emptyRiskSummary(): RiskDashboardSummary {
  return {
    total: 0,
    open: 0,
    automated: 0,
    bySeverity: {
      low: 0,
      medium: 0,
      high: 0,
      critical: 0,
    },
  }
}

function emptyDerivedStatus(system: AISystemSummary): SelectedSystemStatus {
  return {
    readiness: estimateReadiness(system.stage),
    stage: system.stage,
    criticalBlockers: 0,
    failedControls: 0,
    missingEvidence: 0,
    openRisks: 0,
    activeRemediation: 0,
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function deriveLifecycleStage(
  lifecycleStage: AISystemSummary["stage"],
  riskSummary: RiskDashboardSummary,
  evidenceSummary: EvidenceSummaryResponse,
  remediationSummary: RemediationSummaryResponse,
  approvalState: ApprovalStateResponse | null
): AISystemSummary["stage"] {
  if (approvalState?.request?.status === "approved") {
    return "operate"
  }

  if (remediationSummary.active > 0 || remediationSummary.byStatus.blocked) {
    return "remediate"
  }

  if (riskSummary.total > 0 || evidenceSummary.totalEvidence > 0 || approvalState?.request) {
    return "govern"
  }

  return lifecycleStage
}

function deriveReadiness(
  stage: AISystemSummary["stage"],
  riskSummary: RiskDashboardSummary,
  evidenceSummary: EvidenceSummaryResponse,
  remediationSummary: RemediationSummaryResponse,
  approvalState: ApprovalStateResponse | null
) {
  const stageBase: Record<AISystemSummary["stage"], number> = {
    onboard: 18,
    assess: 38,
    govern: 58,
    remediate: 52,
    operate: 88,
  }

  let score = stageBase[stage]
  score += Math.min(evidenceSummary.linkedEvidence * 6, 18)
  score += evidenceSummary.decisionReadiness === "review_ready" ? 14 : 0
  score += approvalState?.request?.status === "approved" ? 10 : 0
  score -= riskSummary.bySeverity.critical * 18
  score -= riskSummary.bySeverity.high * 10
  score -= remediationSummary.active * 8
  score -= Math.max(0, evidenceSummary.missingSignals.length - 1) * 5

  return clamp(Math.round(score), 5, 100)
}

function deriveSystemStatus(
  system: AISystemSummary,
  riskSummary: RiskDashboardSummary,
  evidenceSummary: EvidenceSummaryResponse,
  remediationSummary: RemediationSummaryResponse,
  approvalState: ApprovalStateResponse | null
): SelectedSystemStatus {
  const stage = deriveLifecycleStage(system.stage, riskSummary, evidenceSummary, remediationSummary, approvalState)
  const readiness = deriveReadiness(stage, riskSummary, evidenceSummary, remediationSummary, approvalState)
  const failedControls =
    riskSummary.open +
    remediationSummary.active +
    (evidenceSummary.decisionReadiness === "review_ready" ? 0 : 1)
  const criticalBlockers =
    riskSummary.bySeverity.critical +
    (approvalState?.request?.status === "rejected" ? 1 : 0) +
    (evidenceSummary.decisionReadiness === "needs_evidence" ? 1 : 0)

  return {
    readiness,
    stage,
    criticalBlockers,
    failedControls,
    missingEvidence: evidenceSummary.missingSignals.length,
    openRisks: riskSummary.open,
    activeRemediation: remediationSummary.active,
  }
}

function normalizeSystem(record: AISystemRecord): AISystemSummary {
  const lifecycleSummary = record.lifecycleSummary || {}
  const stage = lifecycleSummary.stage || record.lifecycleStage
  const readiness = typeof lifecycleSummary.readiness === "number"
    ? lifecycleSummary.readiness
    : typeof record.readiness === "number"
      ? record.readiness
      : estimateReadiness(stage)
  return {
    id: record.id,
    name: record.name,
    owner: record.owner || "unassigned",
    riskTier: record.riskTier,
    readiness,
    stage,
    workspaceId: record.workspaceId,
    metadata: {
      ...(record.metadata || {}),
      lifecycleSummary,
    },
  }
}

export function SystemContextProvider({ children }: { children: React.ReactNode }) {
  const [systems, setSystems] = useState<AISystemSummary[]>(FALLBACK_SYSTEMS)
  const [selectedSystemId, setSelectedSystemId] = useState<string>(FALLBACK_SYSTEMS[0].id)
  const [loading, setLoading] = useState(true)
  const [selectedSystemStatus, setSelectedSystemStatus] = useState<SelectedSystemStatus>(
    emptyDerivedStatus(FALLBACK_SYSTEMS[0])
  )

  const refreshSystems = async () => {
    setLoading(true)
    try {
      const response: ApiResponse<AISystemRecord[]> = await apiClient.get(API_ENDPOINTS.aiGovernance.systems)
      if (response.success && response.data && response.data.length > 0) {
        const nextSystems = response.data.map(normalizeSystem)
        setSystems(nextSystems)
        setSelectedSystemId((currentId) => {
          const storedId = getStoredSystemId(nextSystems[0].id)
          const preferredId = currentId || storedId
          const exists = nextSystems.some((system) => system.id === preferredId)
          return exists ? preferredId : nextSystems[0].id
        })
      } else {
        setSystems(FALLBACK_SYSTEMS)
        setSelectedSystemId(getStoredSystemId(FALLBACK_SYSTEMS[0].id))
      }
    } catch {
      setSystems(FALLBACK_SYSTEMS)
      setSelectedSystemId(getStoredSystemId(FALLBACK_SYSTEMS[0].id))
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
  }) => {
    const workspaceResponse: ApiResponse<WorkspaceRecord> = await apiClient.post(
      API_ENDPOINTS.aiGovernance.workspaces,
      {
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
        workspace_id: workspaceResponse.data.id,
        name: params.systemName,
        owner: params.systemOwner,
        risk_tier: params.riskTier,
        lifecycle_stage: params.stage,
        metadata: {
          created_from: "onboard",
          workspace_name: params.workspaceName,
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
    return systems.find((system) => system.id === selectedSystemId) || systems[0] || FALLBACK_SYSTEMS[0]
  }, [selectedSystemId, systems])

  useEffect(() => {
    if (!selectedSystem || selectedSystem.metadata?.source === "fallback") {
      setSelectedSystemStatus(emptyDerivedStatus(selectedSystem || FALLBACK_SYSTEMS[0]))
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

  return (
    <Card className="mb-6 border-4 border-black bg-gradient-to-r from-[#fff4de] via-white to-[#e9f7f0] p-4 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3">
          <div className="border-2 border-black bg-black p-3 text-white shadow-[4px_4px_0px_0px_#FF6B35]">
            <IconBuildingSkyscraper className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
              Current AI System
            </p>
            <h2 className="text-xl font-black uppercase">{selectedSystem.name}</h2>
            <p className="text-sm text-muted-foreground">{selectedSystem.owner}</p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-4 lg:min-w-[720px]">
          <div className="space-y-1">
            <p className="text-xs font-bold uppercase text-muted-foreground">System Scope</p>
            {systems.length > 0 ? (
              <Select onValueChange={setSelectedSystemId} value={selectedSystem.id}>
                <SelectTrigger className="border-2 border-black bg-white font-bold">
                  <SelectValue placeholder={loading ? "Loading systems..." : "Select system"} />
                </SelectTrigger>
                <SelectContent>
                  {systems.map((system) => (
                    <SelectItem key={system.id} value={system.id}>
                      {system.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Button asChild variant="neutral" className="w-full border-2 border-black font-bold">
                <a href="/onboard">
                  <IconPlus className="mr-2 h-4 w-4" />
                  Create system
                </a>
              </Button>
            )}
          </div>

          <div className="space-y-1">
            <p className="text-xs font-bold uppercase text-muted-foreground">Risk Tier</p>
            <Badge className={`border-2 px-3 py-2 font-black uppercase ${riskTierClassName(selectedSystem.riskTier)}`}>
              <IconShieldCheck className="mr-2 h-4 w-4" />
              {selectedSystem.riskTier}
            </Badge>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-bold uppercase text-muted-foreground">Readiness</p>
            <div className="border-2 border-black bg-white px-3 py-2 font-black">
              {selectedSystemStatus.readiness}%
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-bold uppercase text-muted-foreground">Lifecycle Stage</p>
            <Badge className="border-2 border-black bg-black px-3 py-2 font-black uppercase text-white">
              <IconRouteAltLeft className="mr-2 h-4 w-4 text-orange" />
              {selectedSystemStatus.stage}
            </Badge>
          </div>
        </div>
      </div>
    </Card>
  )
}
