export function evidenceSystemHref(systemId: string): string {
  return `/evidence?${new URLSearchParams({ system: systemId })}`
}

export function evidenceRecordHref(systemId: string, evidenceId: string): string {
  return `/evidence?${new URLSearchParams({ system: systemId, evidence: evidenceId })}`
}
