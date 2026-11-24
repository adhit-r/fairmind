export function evaluationHref(evaluationId: string, systemId?: string | null, runId?: string, findingId?: string): string {
  const path = `/compliance/evaluations/${encodeURIComponent(evaluationId)}`
  const query = new URLSearchParams()
  if (systemId) query.set('system', systemId)
  if (runId) query.set('run', runId)
  if (findingId) query.set('finding', findingId)
  return query.size ? `${path}?${query}` : path
}

export function findingHref(systemId: string, findingId: string): string {
  return `/findings?${new URLSearchParams({ system: systemId, finding: findingId })}`
}

/** Missing scope allows a chooser. An empty or repeated identifier is an invalid link. */
export function recordParam(query: Pick<URLSearchParams, 'getAll'>, key: string): string | undefined | null {
  const values = query.getAll(key)
  if (!values.length) return undefined
  const [value] = values
  return values.length === 1 && value && value === value.trim() ? value : null
}
