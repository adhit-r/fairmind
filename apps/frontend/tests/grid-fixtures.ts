import type { Page, Route } from '@playwright/test'

// Network fixtures for the grid specs: the browser's API calls are answered here, nothing reaches a database.
const FW = 'ISO42001'
const confirmed = {
  rulesVersion: '1', answers: {}, suggestedTier: 'high', tier: 'high', tierRules: [], suggestedFrameworks: [FW],
  frameworks: [{ key: FW, name: 'ISO/IEC 42001:2023' }], added: [], removed: [], reason: null, tierBelowSuggestion: false,
  overrideAcceptedBy: null, overrideAcceptedAt: null, confirmedBy: 'reviewer', confirmedAt: '2026-11-01T00:00:00Z', evidenceId: 'ev-app',
}
const systems = [
  { id: 'sys-a', workspaceId: 'ws-1', name: 'Grid system A', owner: 'owner-a', riskTier: 'high', lifecycleStage: 'govern', metadata: { applicability: confirmed }, createdAt: '2026-10-01T00:00:00Z', updatedAt: '2026-10-01T00:00:00Z' },
  { id: 'sys-b', workspaceId: 'ws-1', name: 'Grid system B', owner: 'owner-b', riskTier: 'low', lifecycleStage: 'remediate', metadata: {}, createdAt: '2026-10-02T00:00:00Z', updatedAt: '2026-10-02T00:00:00Z' },
]
const check = (key: string, label: string, state: string, evidenceClass: string | null, extra: Record<string, unknown> = {}) => ({
  key, label, state, confidence: state === 'open' ? 0 : 0.9, evidenceId: state === 'open' ? null : `ev-${key}`, evidenceClass, ...extra,
})
const checks = [
  check('fairness', 'Fairness', 'proven', 'measured', { fails: true }),
  check('data_governance', 'Data governance', 'attested', 'manual'),
  check('human_oversight', 'Human oversight', 'proven', 'tool_estimated'),
  check('monitoring', 'Monitoring', 'open', null, { stale: true }),
  check('environmental', 'Environmental', 'open', null),
]
const gates = systems.map((s, i) => ({ systemId: s.id, verdict: i ? 'no_go' : 'conditional_go', confidence: i ? 0.2 : 0.55, band: 'estimated', approvalStatus: 'not_requested', checks }))
const req = (control: string, title: string, status: string) => ({ key: `${FW}|${control}`, control, title, status, workflows: [], evaluations: [] })
const journey = {
  key: FW, name: 'ISO/IEC 42001:2023', pillar: 'governance', version: null, type: null, binding: null, status: null, active: 3, coveredAll: 0, coveredInstalled: 0,
  groups: [
    { name: 'Clause 4 Context', requirements: [req('4.1', 'Organisation and its context', 'covered'), req('4.2', 'Interested parties', 'gap')] },
    { name: 'Clause 9 Performance', requirements: [req('9.1', 'Monitoring and measurement', 'available')] },
  ],
  steps: [],
}
const frameworkSystems = {
  framework: { key: FW, name: 'ISO/IEC 42001:2023' },
  systems: [{ id: 'sys-a', name: 'Grid system A', riskTier: 'high' }],
  unconfirmed: 1,
  notInScope: 0,
  requirements: [
    { key: `${FW}|4.1`, cells: [{ state: 'proven', checks: [{ check: 'fairness', label: 'Fairness', relation: 'Supports', confidence: 0.9, evidenceId: 'ev-fairness', evidenceClass: 'measured' }] }] },
    { key: `${FW}|9.1`, cells: [{ state: 'open', checks: [] }] },
  ],
}
const controls = {
  controls: [{ id: 'FMC-MON-01', name: 'Monitoring', objective: 'Watch the system in production.', workflows: [] }],
  crosswalk: [{ commonControl: 'FMC-MON-01', key: `${FW}|9.1`, relation: 'Satisfies' }],
}

const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

export const GRID_FW = FW
/** One system per tier, so every tier is a one-column group beside another. */
export const ONE_PER_TIER = {
  ...frameworkSystems,
  systems: [
    { id: 'sys-a', name: 'Grid system A', riskTier: 'critical' },
    { id: 'sys-c', name: 'Grid system C', riskTier: 'high' },
    { id: 'sys-d', name: 'Grid system D', riskTier: 'medium' },
  ],
  requirements: frameworkSystems.requirements.map((r) => ({ ...r, cells: [r.cells[0], r.cells[0], r.cells[0]] })),
}

export async function installGridFixtures(page: Page, fwSystems: unknown = frameworkSystems) {
  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
  })
  await page.route('**/api/proxy/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
    if (path === '/api/v1/auth/me') return json(route, { id: 'user-1', username: 'reviewer', email: 'reviewer@grid.test' })
    if (path === '/api/v1/organizations') return json(route, { organizations: [{ id: 'org-1', name: 'Grid org', slug: 'grid-org', owner_id: 'user-1', created_at: '2026-01-01T00:00:00Z', role: 'admin' }] })
    if (path === '/api/v1/ai-governance/systems') return json(route, systems)
    if (path === '/api/v1/ai-governance/estate/gates') return json(route, gates)
    if (path === `/api/v1/ai-governance/frameworks/${FW}/systems`) return json(route, fwSystems)
    if (path === `/api/v1/packs/journeys/${FW}`) return json(route, journey)
    if (path === '/api/v1/packs/journeys') return json(route, [{ key: FW, name: journey.name }])
    if (path === '/api/v1/packs/controls') return json(route, controls)
    return json(route, [])
  })
}

/** Cards below the command bar, the legend count and page overflow, as the declutter rules state them. */
export async function layoutFacts(page: Page) {
  return page.evaluate(() => ({
    cards: document.querySelectorAll('main .fm-card:not(.fm-cmd)').length,
    legends: document.querySelectorAll('.mx-legend').length,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  }))
}
