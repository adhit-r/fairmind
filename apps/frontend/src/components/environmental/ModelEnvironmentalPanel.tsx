'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { IconLeaf, IconAlertTriangle } from '@tabler/icons-react'
import { apiClient, type ApiResponse } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { useGovernedSystemForModel } from '@/lib/api/hooks/useEnvironmentalAssessment'
import { EnvironmentalAssessmentWorkbench } from './EnvironmentalAssessmentWorkbench'

/**
 * Environmental governance for a model under evaluation.
 *
 * Models and governed systems are separate entities: a model is an artifact,
 * a governed system is the governance record that carries risks, evidence,
 * approvals, and the environmental release gate. This panel resolves the link
 * and, when a model is not yet governed, offers to create that record so the
 * reviewer can act without leaving the evaluation flow.
 */
export function ModelEnvironmentalPanel({
  modelId,
  modelName,
}: {
  modelId: string
  modelName?: string
}) {
  const { systemId, governed, loading, error, refetch } = useGovernedSystemForModel(modelId)
  const [registering, setRegistering] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)

  const registerForGovernance = async () => {
    setRegistering(true)
    setRegisterError(null)
    try {
      // A governed system lives in a workspace. Reuse the first available one
      // rather than inventing a workspace silently; if none exists the user is
      // told to create one in AI Governance, because workspace ownership is a
      // governance decision and not ours to make here.
      const workspacesResponse: ApiResponse<Array<{ id: string; name?: string }>> =
        await apiClient.get(API_ENDPOINTS.aiGovernance.workspaces)
      const workspaces = Array.isArray(workspacesResponse.data) ? workspacesResponse.data : []
      if (!workspacesResponse.success || workspaces.length === 0) {
        throw new Error(
          'No governance workspace exists yet. Create one in AI Governance, then register this model.'
        )
      }

      const created: ApiResponse<{ id?: string }> = await apiClient.post(
        API_ENDPOINTS.aiGovernance.systems,
        {
          workspace_id: workspaces[0].id,
          name: modelName || `Model ${modelId}`,
          risk_tier: 'medium',
          lifecycle_stage: 'assess',
          metadata: { source: 'model_evaluation' },
          model_id: modelId,
        }
      )
      if (!created.success) {
        throw new Error(created.error || 'Failed to register the model for governance')
      }
      await refetch()
    } catch (err) {
      setRegisterError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setRegistering(false)
    }
  }

  if (loading) {
    return (
      <Card className="p-6 border-2 border-black shadow-brutal">
        <p className="text-sm font-bold uppercase tracking-wider">Resolving governance record...</p>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert className="border-2 border-black shadow-brutal">
        <IconAlertTriangle className="h-4 w-4" />
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    )
  }

  if (!governed || !systemId) {
    return (
      <Card className="p-6 border-2 border-black shadow-brutal space-y-4">
        <div className="flex items-center gap-2">
          <IconLeaf className="h-5 w-5" />
          <h2 className="text-xl font-black uppercase tracking-tight">Environmental Impact</h2>
        </div>
        <p className="font-bold">This model is not registered for governance.</p>
        <p className="text-sm text-muted-foreground">
          Environmental assessments attach to a governed system, which also carries the model&apos;s
          risks, evidence, and release approvals. Register this model to run an assessment and put
          it behind the environmental release gate.
        </p>
        {registerError && (
          <Alert className="border-2 border-black">
            <IconAlertTriangle className="h-4 w-4" />
            <AlertDescription>{registerError}</AlertDescription>
          </Alert>
        )}
        <Button
          className="border-2 border-black shadow-brutal font-bold"
          onClick={registerForGovernance}
          disabled={registering}
        >
          {registering ? 'Registering...' : 'Register for governance'}
        </Button>
      </Card>
    )
  }

  return <EnvironmentalAssessmentWorkbench systemId={systemId} />
}
