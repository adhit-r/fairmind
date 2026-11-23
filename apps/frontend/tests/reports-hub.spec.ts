import { expect, test, type Page, type Route } from '@playwright/test'

// The browser's API calls are answered here, nothing reaches a database.
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

const base = (role: string) => ({
  role,
  scope: { systemId: null, systemName: null },
  framework: { key: 'ISO42001', name: 'ISO/IEC 42001:2023' },
  followed: ['ISO42001'],
  systemsCount: 2,
  generatedAt: '2026-11-22T10:00:00Z',
  briefing: {
    source: 'template',
    parts: [
      { text: 'Acme meets ' },
      { fact: 'Readiness', value: '62%', note: 'Requirements met across all systems', tone: '' },
      { text: ' of its requirements and ' },
      { fact: 'Acme claims agent', value: 'is blocked', note: 'Fails the security check', tone: 'bad' },
      { text: '.' },
    ],
  },
})

const executive = {
  ...base('executive'),
  readiness: { met: 31, progress: 10, attention: 4, notstarted: 15, total: 60, pct: 62, systems: 2 },
  road: {
    start: 62,
    forecast: 71,
    steps: [
      { systemId: 's1', systemName: 'Acme loan model', check: 'human_oversight', action: 'Run the oversight evaluation', evidenceClass: 'measured', closes: ['A.9.2', 'A.9.3'], gain: 5, owner: 'Acme Owner' },
      { systemId: 's2', systemName: 'Acme claims agent', check: 'security', action: 'Gate the refund tool', evidenceClass: 'attested', closes: ['A.6.2.4'], gain: 4, owner: null },
    ],
  },
  proof: { measured: 24, estimated: 6, attested: 21, none: 9, bySystem: [{ systemId: 's1', name: 'Acme loan model', measured: 12, estimated: 3, attested: 9, none: 4 }], byGroup: [] },
  governed: { found: 9, registered: 6, checked: 4, approved: 2, unregistered: [{ name: 'Acme chat tool', kind: 'saas', source: 'okta' }], unregisteredCount: 1 },
  oversight: { days: [{ date: '2026-11-20', agentSteps: 30, decisions: 2 }, { date: '2026-11-21', agentSteps: 12, decisions: 0 }], agentSteps: 42, decisions: 2, medianWaitHours: null, approvedWithoutPerson: 0 },
  decisions: [{ id: 'd1', systemName: 'Acme loan model', requestedBy: 'Acme Owner', waitingDays: 3 }],
  risk: { risks: [], heat: [], acceptanceWaiting: [] },
}

const risk = {
  ...base('risk'),
  risk: {
    risks: [
      { id: 'r1', title: 'Acme refund tool misuse', systemName: 'Acme claims agent', severity: 'high', likelihood: 'likely', impact: 4, chance: 4, status: 'open', owner: 'Acme Owner' },
    ],
    heat: [{ chance: 4, impact: 4, count: 1 }],
    acceptanceWaiting: [],
  },
}

const engineering = {
  ...base('engineering'),
  outOfScope: 8,
  briefing: {
    source: 'template',
    parts: [
      { fact: 'systems.nogo', value: '2', note: 'Systems whose release gate verdict is No go', tone: 'bad' },
      { text: ' of ' },
      { fact: 'systems.listed', value: '2', note: 'Systems listed in the release gate table', tone: '' },
      { text: ' systems in scope are not cleared for release.' },
    ],
  },
  systems: [
    { id: 's1', name: 'Acme loan model', tier: 'high', verdict: 'no_go', approvalStatus: null, confidence: 0.2, checks: [{ key: 'fairness', label: 'Fairness measured', state: 'open', fails: false, stale: false }] },
    { id: 's2', name: 'Acme claims agent', tier: 'high', verdict: 'no_go', approvalStatus: null, confidence: 0.1, checks: [{ key: 'fairness', label: 'Fairness measured', state: 'open', fails: true, stale: false }] },
  ],
  engineering: {
    toolExposure: [],
    fairnessDrift: [],
    fixes: [{ title: 'EV-SEC-14 Model file and dependency scanning failed', systemName: 'Acme claims agent', priority: 'high', status: 'open', owner: null, kind: 'evaluation', evaluationId: 'EV-SEC-14', summary: '2 unpinned packages' }],
  },
}

const sealed = { id: 'snap-1', title: 'Executive summary', role: 'executive', systemId: null, sha256: 'b84e'.repeat(16), approvedBy: 'reviewer', approvedAt: '2026-11-22T10:05:00Z' }

async function install(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
  })
  await page.route('**/api/proxy/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace('/api/proxy', '')
    const method = route.request().method()
    if (path === '/api/v1/auth/me') return json(route, { id: 'user-1', username: 'reviewer', email: 'reviewer@acme.test' })
    if (path === '/api/v1/organizations') return json(route, { organizations: [{ id: 'org-1', name: 'Acme org', slug: 'acme-org', owner_id: 'user-1', created_at: '2026-01-01T00:00:00Z', role: 'admin' }] })
    if (path === '/api/v1/ai-governance/reports/overview') {
      const role = url.searchParams.get('role')
      return json(route, role === 'risk' ? risk : role === 'engineering' ? engineering : executive)
    }
    if (path === '/api/v1/ai-governance/reports/briefing') return json(route, { source: 'template', parts: [] })
    if (path === '/api/v1/ai-governance/reports/snapshots') return json(route, method === 'POST' ? sealed : [])
    if (path === '/api/v1/shadow-ai') return json(route, { findings: [], resolved: [], map: { tools: [], teams: [], cells: {} }, coverage: { proxyLogs: false, okta: false, entra: false, gateway: false, mcpRegistry: false, people: 0, approvedTools: 0, ssoTools: 0 } })
    return json(route, [])
  })
}

test.describe('Reports hub', () => {
  test.beforeEach(async ({ page }) => install(page))

  test('executive shows the road to the audit and the briefing chips', async ({ page }) => {
    await page.goto('/reports')
    await expect(page.getByRole('heading', { name: 'Road to the audit' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText('Run the oversight evaluation')).toBeVisible()
    await expect(page.getByText('Unassigned', { exact: false }).first()).toBeVisible()
    await expect(page.getByText('Written from the record')).toBeVisible()
    const chip = page.locator('.rp-cite', { hasText: '62%' })
    await expect(chip).toHaveAttribute('title', 'Requirements met across all systems')
    await expect(page.locator('.rp-cite.bad')).toHaveText('is blocked')
  })

  test('switching to Risk shows the heat map', async ({ page }) => {
    await page.goto('/reports')
    await expect(page.getByRole('heading', { name: 'Road to the audit' })).toBeVisible({ timeout: 30_000 })
    await page.getByRole('radio', { name: 'Risk' }).click()
    await expect(page).toHaveURL(/role=risk/)
    await expect(page.getByRole('heading', { name: 'Heat map' })).toBeVisible()
    await expect(page.getByLabel(/Likely, critical impact/)).toBeVisible()
  })

  test('engineering lists in-scope systems and shows a failed evaluation as a fix', async ({ page }) => {
    await page.goto('/reports?role=engineering')
    await expect(page.getByRole('heading', { name: 'Release gate checks' })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText(/8 registered systems are outside its scope and not listed/)).toBeVisible()
    await expect(page.locator('.rp-cite', { hasText: '2' }).first()).toBeVisible()
    await expect(page.getByText('EV-SEC-14 Model file and dependency scanning failed')).toBeVisible()
    await expect(page.getByText('Run it again once fixed')).toBeVisible()
  })

  test('approving in the drawer shows the seal', async ({ page }) => {
    await page.goto('/reports')
    await expect(page.getByRole('heading', { name: 'Road to the audit' })).toBeVisible({ timeout: 30_000 })
    await page.getByRole('button', { name: 'Download report' }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog.getByText('Nothing is sealed until you approve')).toBeVisible()
    await expect(dialog.getByLabel('Summary on page one')).toContainText('Acme meets 62%')
    await dialog.getByRole('button', { name: 'Approve and seal' }).click()
    await expect(dialog.getByText('Sealed', { exact: true })).toBeVisible()
    await expect(dialog.getByText(sealed.sha256)).toBeVisible()
    await expect(dialog.getByRole('button', { name: /Download Executive summary as PDF/ })).toBeVisible()
  })
})
