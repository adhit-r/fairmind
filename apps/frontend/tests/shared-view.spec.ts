import { expect, test, type Page, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
const VIEW = '5b1f5a46-7b1e-4a58-9d5e-0c6b0e3c2a11'
const PUBLIC = new RegExp(`/api/proxy/api/v1/public/shared-views/${VIEW}(/[a-z]+)?$`)
const check = (key: string, label: string, state: string, evidenceClass: string | null, extra: Record<string, unknown> = {}) => ({
  key, label, state, confidence: state === 'open' ? 0 : 0.9, evidenceId: state === 'open' ? null : `ev-${key}`, evidenceClass, ...extra,
})
// What the server sealed: the responses of the reads the board makes, keyed by their path.
const sealed = {
  '/api/v1/ai-governance/systems': [{ id: 'sys-a', workspaceId: 'ws-1', name: 'Sealed system A', owner: 'owner-a', riskTier: 'high', lifecycleStage: 'govern', metadata: {}, createdAt: '2026-10-01T00:00:00Z', updatedAt: '2026-10-01T00:00:00Z' }],
  '/api/v1/ai-governance/estate/gates?org_id=org-1': [{ systemId: 'sys-a', verdict: 'no_go', confidence: 0.2, band: 'estimated', approvalStatus: 'not_requested', checks: [check('fairness', 'Fairness', 'proven', 'measured', { fails: true }), check('monitoring', 'Monitoring', 'open', null)] }],
}
const content = {
  question: 'Which systems fail?', board: 'root = Board([m])\nm = ReleaseMatrix("all")', orgId: 'org-1', data: sealed,
  sealedAt: '2026-11-28T14:02:00Z', seal: '8f3a9c1d5e7b2a4c6d8e0f1a3b5c7d9e1f2a4b6c8d0e2f4a6b8c0d2e4f6a8c21', expiresAt: '2026-12-28T14:02:00Z',
}

/** Answers the public routes of one view and counts what reached the app's own endpoints. */
async function reading(page: Page, access: 'named' | 'link', reached: string[]) {
  await page.route('**/api/proxy/**', (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
    if (!path.includes('/public/shared-views/')) reached.push(path)
    return json(route, [])
  })
  await page.route(PUBLIC, (route) => {
    const step = new URL(route.request().url()).pathname.split('/').pop()
    if (step === VIEW) return json(route, { access, expiresAt: content.expiresAt })
    if (step === 'code') return json(route, { sent: true })
    if (step === 'verify') return json(route, { token: 't' }, route.request().postDataJSON().code === '123456' ? 200 : 401)
    if (step === 'open') return json(route, { token: 't' })
    if (step === 'seal') return json(route, { matchesStored: true, onLedger: true, ledgerSeq: 3, ledgerHash: 'h', ledgerAt: '2026-11-28T14:02:01Z', chainValid: true })
    return route.request().headers()['x-view-token'] ? json(route, content) : json(route, { detail: 'Open the view again to continue' }, 401)
  })
}

test.describe('Shared view', () => {
  test('a named reader asks for a code, then reads the sealed figures without reaching the app', async ({ page }) => {
    const reached: string[] = []
    await reading(page, 'named', reached)
    await page.goto(`/view/${VIEW}`)
    await page.getByRole('textbox', { name: 'Email address' }).fill('auditor@example.com')
    await page.getByRole('button', { name: 'Send code' }).click()
    await page.getByRole('textbox', { name: 'Code' }).fill('000000')
    await page.getByRole('button', { name: 'Open', exact: true }).click()
    await expect(page.getByText('That code did not work')).toBeVisible()
    await page.getByRole('textbox', { name: 'Code' }).fill('123456')
    await page.getByRole('button', { name: 'Open', exact: true }).click()

    const board = page.getByRole('region', { name: 'Release checks' })
    await expect(board.getByText('Sealed system A')).toBeVisible({ timeout: 30_000 })
    await expect(board.getByRole('link')).toHaveCount(0) // the reader has no pages to go to
    await expect(page.getByText('Sealed snapshot')).toBeVisible()
    await expect(page.getByText(/sha256 8f3a9c1d/)).toBeVisible()
    await expect(page.getByText('does not certify compliance')).toBeVisible()
    await page.getByRole('button', { name: 'Verify seal' }).click()
    await expect(page.getByText("matches entry 3 on the organisation's ledger")).toBeVisible()
    expect(reached).toEqual([]) // every figure came from the seal
  })

  test('a link view opens at once, and a closed one says so', async ({ page }) => {
    await reading(page, 'link', [])
    await page.goto(`/view/${VIEW}`)
    await expect(page.getByRole('region', { name: 'Release checks' }).getByText('Sealed system A')).toBeVisible({ timeout: 30_000 })

    const gone = await page.context().newPage()
    await gone.route('**/api/proxy/**', (route) => json(route, { detail: 'This view is not available' }, 404))
    await gone.goto(`/view/${VIEW}`)
    await expect(gone.getByRole('heading', { name: 'This view is not available' })).toBeVisible()
  })

  test('sharing from Ask sends the board, who may open it and the figures it read, never a figure', async ({ page }) => {
    await installGridFixtures(page)
    await page.route(/\/api\/v1\/packs\/ai-provider(\?|$)/, (route) => json(route, { config: { provider: 'anthropic', providerName: 'Anthropic', model: 'm', hasKey: true, keyHint: null, keyReadable: true, enabled: true, testedOk: true, testedAt: null, testMessage: null, updatedAt: null } }))
    await page.route(/\/api\/v1\/packs\/ask(\?|$)/, (route) => json(route, { answer: 'Two systems need attention.', board: content.board, systems: [], provider: 'Anthropic', model: 'm', systemsRead: 2, runsRead: 0 }))
    let posted: { access: string; emails: string[]; days: number; paths: string[]; board: string } | null = null
    await page.route(/\/api\/v1\/packs\/shared-views(\?|$)/, (route) => {
      if (route.request().method() === 'POST') {
        posted = route.request().postDataJSON()
        return json(route, { id: VIEW, link: `http://localhost/view/${VIEW}`, expiresAt: content.expiresAt, sealedAt: content.sealedAt })
      }
      return json(route, { views: [] })
    })
    await page.goto('/ask')
    await page.getByRole('textbox').fill('Which systems fail?')
    await page.keyboard.press('Enter')
    await expect(page.getByText('Two systems need attention.')).toBeVisible({ timeout: 30_000 })

    await page.getByRole('button', { name: 'Share as a view' }).click()
    const create = page.getByRole('button', { name: 'Create view' })
    await expect(create).toBeDisabled() // nobody named yet
    await page.getByRole('textbox', { name: 'Email addresses' }).fill('auditor@example.com, reviewer@example.com')
    await expect(create).toBeEnabled({ timeout: 30_000 })
    await create.click()
    await expect(page.getByText(`/view/${VIEW}`)).toBeVisible()

    expect(posted).not.toBeNull()
    expect(posted!.access).toBe('named')
    expect(posted!.emails).toEqual(['auditor@example.com', 'reviewer@example.com'])
    expect(posted!.days).toBe(30)
    expect(posted!.board).toBe(content.board)
    expect(posted!.paths.some((p) => p.startsWith('/api/v1/ai-governance/estate/gates'))).toBe(true)
    expect(posted!.paths.some((p) => p.includes('/boards') || p.includes('shared-views'))).toBe(false)
    expect(Object.keys(posted!)).not.toContain('data') // the server reads the figures, not the browser
  })
})
