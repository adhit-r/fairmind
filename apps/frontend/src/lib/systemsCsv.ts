import { parseCsv } from './csvRows'

export const TIERS = ['low', 'medium', 'high', 'critical'] as const
export const STAGE_KEYS = ['onboard', 'assess', 'govern', 'remediate', 'operate'] as const

export type SystemRow = {
  line: number
  name: string
  owner: string
  riskTier: (typeof TIERS)[number]
  stage: (typeof STAGE_KEYS)[number]
  businessLine?: string
  version?: string
}

/** The header a systems CSV needs, offered as a template. */
export const SYSTEMS_CSV_TEMPLATE = 'name,owner,risk_tier,stage,business_line,version\n'

const pick = (row: Record<string, string | number>, ...keys: string[]) => {
  for (const k of keys) {
    const v = row[k]
    if (v != null && String(v).trim() !== '') return String(v).trim()
  }
  return ''
}

/**
 * Read a CSV of AI systems: one per row, `name` and `risk_tier` required, `stage` defaulting to onboard.
 * Rows that cannot be registered come back as problems with their line number, so nothing is dropped silently.
 */
export function readSystemsCsv(text: string): { rows: SystemRow[]; problems: { line: number; message: string }[] } {
  const { header, rows: raw } = parseCsv(text, 1000)
  const lower = raw.map((r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k.toLowerCase().replace(/\s+/g, '_'), v])))
  const problems: { line: number; message: string }[] = []
  if (!header.length) return { rows: [], problems: [{ line: 1, message: 'The file is empty.' }] }
  const rows: SystemRow[] = []
  const seen = new Set<string>()
  lower.forEach((r, i) => {
    const line = i + 2
    const name = pick(r, 'name', 'system', 'system_name')
    const tier = pick(r, 'risk_tier', 'tier', 'risk').toLowerCase()
    const stage = (pick(r, 'stage', 'lifecycle_stage') || 'onboard').toLowerCase()
    if (!name) return problems.push({ line, message: 'No name.' })
    if (seen.has(name.toLowerCase())) return problems.push({ line, message: `"${name}" appears twice in this file.` })
    if (!TIERS.includes(tier as SystemRow['riskTier'])) return problems.push({ line, message: `Risk tier must be low, medium, high or critical (got "${tier || 'nothing'}").` })
    if (!STAGE_KEYS.includes(stage as SystemRow['stage'])) return problems.push({ line, message: `Stage must be one of ${STAGE_KEYS.join(', ')} (got "${stage}").` })
    seen.add(name.toLowerCase())
    rows.push({
      line,
      name,
      owner: pick(r, 'owner', 'system_owner'),
      riskTier: tier as SystemRow['riskTier'],
      stage: stage as SystemRow['stage'],
      businessLine: pick(r, 'business_line', 'line') || undefined,
      version: pick(r, 'version') || undefined,
    })
  })
  return { rows, problems }
}
