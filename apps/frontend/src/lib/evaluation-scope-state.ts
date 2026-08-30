export type EvaluationScopeIdentity = {
  organizationId?: string | null
  workspaceId?: string | null
  systemId?: string | null
  planId?: string | null
  runId?: string | null
}

export type EvaluationScopeState<T> = {
  scopeKey: string
  value: T
}

export function evaluationScopeKey(scope: EvaluationScopeIdentity) {
  return JSON.stringify([
    scope.organizationId ?? null,
    scope.workspaceId ?? null,
    scope.systemId ?? null,
    scope.planId ?? null,
    scope.runId ?? null,
  ])
}

export function readEvaluationScopeState<T>(
  state: EvaluationScopeState<T>,
  currentScopeKey: string,
  maskedValue: T,
) {
  return state.scopeKey === currentScopeKey ? state.value : maskedValue
}

export function writeEvaluationScopeState<T>(
  current: EvaluationScopeState<T>,
  expectedScopeKey: string,
  value: T,
) {
  return current.scopeKey === expectedScopeKey
    ? { scopeKey: expectedScopeKey, value }
    : current
}
