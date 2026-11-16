"use client"

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"

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

/**
 * Placeholder returned by the legacy `selectedSystem` field when no real AI
 * system is available (not loaded yet, load failed, or the org has none).
 * It carries an empty id so callers can detect it. It is NOT a real system and
 * must never be rendered as scope. New code should use `activeSystem`
 * (null when there is no real system) instead.
 */
export const NO_SYSTEM: AISystemSummary = {
  id: "",
  name: "No AI system selected",
  owner: "",
  riskTier: "low",
  readiness: 0,
  stage: "onboard",
  metadata: { source: "none" },
}

export function isRealSystem(system: AISystemSummary | null | undefined): system is AISystemSummary {
  return Boolean(system && system.id)
}

type SystemContextValue = {
  systems: AISystemSummary[]
  /** The selected real AI system, or null when none is available. */
  activeSystem: AISystemSummary | null
  /** Why systems could not be loaded (null when the load succeeded). */
  systemsError: string | null
  /**
   * Legacy: always defined. Equals NO_SYSTEM (empty id) when there is no real
   * system. Prefer `activeSystem`.
   */
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
    systemType?: string
    systemVersion?: string
    complianceFrameworks?: string[]
  }) => Promise<AISystemSummary>
}

const SystemContext = createContext<SystemContextValue | null>(null)

function getStoredSystemId() {
  if (typeof window === "undefined") {
    return null
  }
  return window.localStorage.getItem("fairmind:selected-ai-system")
}

export function chooseSelectedSystemId(
  systemIds: string[],
  currentId: string,
  storedId: string | null,
) {
  if (storedId && systemIds.includes(storedId)) return storedId
  if (systemIds.includes(currentId)) return currentId
  return systemIds[0] ?? ""
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
  const [systems, setSystems] = useState<AISystemSummary[]>([])
  const [selectedSystemId, setSelectedSystemId] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [systemsError, setSystemsError] = useState<string | null>(null)
  const [selectedSystemStatus, setSelectedSystemStatus] = useState<SelectedSystemStatus>(
    emptyDerivedStatus(NO_SYSTEM)
  )

  const refreshSystems = async () => {
    setLoading(true)
    try {
      const response: ApiResponse<AISystemRecord[]> = await apiClient.get(API_ENDPOINTS.aiGovernance.systems)
      if (response.success && Array.isArray(response.data)) {
        setSystemsError(null)
        const nextSystems = response.data.map(normalizeSystem)
        setSystems(nextSystems)
        setSelectedSystemId((currentId) => {
          return chooseSelectedSystemId(
            nextSystems.map((system) => system.id),
            currentId,
            getStoredSystemId(),
          )
        })
      } else {
        setSystems([])
        setSelectedSystemId("")
        setSystemsError(response.error || "AI systems could not be loaded.")
      }
    } catch (error) {
      setSystems([])
      setSelectedSystemId("")
      setSystemsError(error instanceof Error ? error.message : "AI systems could not be loaded.")
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
    complianceFrameworks?: string[]
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
          ...(params.systemType && { system_type: params.systemType }),
          ...(params.systemVersion && { system_version: params.systemVersion }),
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
    setSystemsError(null)
    setAndPersist(nextSystem.id)
    return nextSystem
  }

  const selectedSystem = useMemo(() => {
    return systems.find((system) => system.id === selectedSystemId) || systems[0] || NO_SYSTEM
  }, [selectedSystemId, systems])

  useEffect(() => {
    if (!isRealSystem(selectedSystem)) {
      setSelectedSystemStatus(emptyDerivedStatus(NO_SYSTEM))
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
        activeSystem: isRealSystem(selectedSystem) ? selectedSystemWithStatus : null,
        systemsError,
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
