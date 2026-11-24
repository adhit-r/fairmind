import { recordParam } from './evaluationLinks'

/** Keep an absent scope distinct from a malformed scope, which the API rejects. */
export function packSystem(search: { getAll(name: string): string[] }): string | undefined {
  const requested = recordParam(search, 'system')
  return requested === null ? '' : requested
}

export function withPackSystem(path: string, system?: string | null): string {
  if (system == null) return path
  return `${path}${path.includes('?') ? '&' : '?'}system=${encodeURIComponent(system)}`
}
