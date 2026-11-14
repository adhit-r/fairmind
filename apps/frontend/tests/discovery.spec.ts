import { expect, test, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

// Discovery overview, source monitoring and the connect flow; API calls are answered here, nothing reaches a database.
const BASE = '/api/v1/integrations'
const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
const minsAgo = (m: number) => new Date(Date.now() - m * 60_000).toISOString()
const minsAhead = (m: number) => new Date(Date.now() + m * 60_000).toISOString()
const run = (id: string, m: number, status: 'ok' | 'failed', found: number, created: number, names: string[] = [], error: string | null = null) => ({
  id, trigger: 'schedule', startedAt: minsAgo(m), finishedAt: minsAgo(m), status, found, created, updated: found - created, error, newNames: names,
})
const integrations = [
  {
    id: 'i-okta', kind: 'okta', name: 'Company Okta', config: { domain: 'acme.okta.com', schedule_minutes: 60 }, hasToken: true,
    lastSyncedAt: minsAgo(12), lastSync: null, createdAt: minsAgo(3000), scheduleMinutes: 60, nextSyncAt: minsAhead(48),
    recentRuns: [run('r3', 12, 'ok', 4, 1, ['Perplexity']), run('r2', 72, 'ok', 3, 0), run('r1', 132, 'ok', 3, 3)],
  },
  {
    id: 'i-aws', kind: 'aws', name: 'Prod AWS', config: { access_key_id: 'AKIA', schedule_minutes: 1440 }, hasToken: true,
    lastSyncedAt: minsAgo(1500), lastSync: null, createdAt: minsAgo(3000), scheduleMinutes: 1440, nextSyncAt: minsAgo(60),
    recentRuns: [run('a2', 30, 'failed', 0, 0, [], 'AWS rejected the credentials (InvalidClientTokenId)'), run('a1', 1500, 'ok', 6, 6)],
  },
  { id: 'i-logs', kind: 'proxy_logs', name: 'Zscaler export', config: {}, hasToken: false, lastSyncedAt: null, lastSync: null, createdAt: minsAgo(10), scheduleMinutes: 0, nextSyncAt: null, recentRuns: [] },
]
const asset = (id: string, source: string, name: string, kind: string, status: string, metadata: Record<string, unknown>) => ({
  id, integrationId: 'i-okta', source, externalId: id, name, kind, metadata, suggestedTier: 'medium', suggestedStage: 'onboard', status, systemId: null, discoveredAt: minsAgo(12),
})
const discovered = [
  asset('okta:a1', 'okta', 'ChatGPT Enterprise', 'ai_service', 'new', { service: 'ChatGPT', vendor: 'OpenAI', distinct_users_30_days: 42 }),
  asset('aws:x', 'aws', 'claims-agent', 'agent', 'promoted', { service: 'Bedrock Agents' }),
]

test.describe('Discovery', () => {
  let created: Record<string, unknown> | null
  let patched: Record<string, unknown> | null
  let previewed: Record<string, unknown> | null
  let synced: string[]
  let uploaded: string | null

  test.beforeEach(async ({ page }) => {
    created = patched = previewed = uploaded = null
    synced = []
    await installGridFixtures(page)
    await page.route('**/api/proxy/**', async (route) => {
      const req = route.request()
      const path = new URL(req.url()).pathname.replace('/api/proxy', '')
      if (path === BASE && req.method() === 'GET') return json(route, integrations)
      if (path === BASE && req.method() === 'POST') {
        created = req.postDataJSON()
        return json(route, { ...integrations[0], id: 'i-new', ...created }, 201)
      }
      if (path === `${BASE}/preview`) {
        previewed = req.postDataJSON()
        return json(route, { found: 9, byKind: { llm_app: 7, agent: 2 }, sample: [{ name: 'anthropic.claude-opus', kind: 'llm_app', tier: 'medium' }, { name: 'claims-agent', kind: 'agent', tier: 'high' }] })
      }
      if (path === `${BASE}/i-okta` && req.method() === 'PATCH') {
        patched = req.postDataJSON()
        return json(route, integrations[0])
      }
      const sync = path.match(/^\/api\/v1\/integrations\/([^/]+)\/sync$/)
      if (sync) {
        synced.push(sync[1])
        return json(route, { found: 1, created: 1, updated: 0, at: minsAgo(0) })
      }
      if (path === `${BASE}/i-logs/upload`) {
        uploaded = req.postDataJSON().text
        return json(route, { found: 2, created: 2, updated: 0, at: minsAgo(0) })
      }
      if (path === `${BASE}/discovered`) return json(route, discovered)
      return route.fallback()
    })
  })

  test('overview shows watched and unwatched areas and what waits', async ({ page }) => {
    await page.goto('/discovery')
    const areas = page.getByRole('region', { name: 'Where AI can show up' })
    await expect(areas.getByRole('button', { name: /Sign-in and workplace.*1 found/ })).toBeVisible()
    await expect(areas.getByRole('button', { name: /MCP servers.*Not watched/ })).toBeVisible()
    await expect(page.getByText('1 registered')).toBeVisible()
    await expect(page.getByText('42 people signed in')).toBeVisible()
    await areas.getByRole('button', { name: /Cloud/ }).click()
    await expect(page.getByText('Nothing waiting from this area.')).toBeVisible()
  })

  test('sources view shows live state, failures and changes the schedule', async ({ page }) => {
    await page.goto('/discovery?view=sources')
    const okta = page.locator('.dv-src', { hasText: 'Company Okta' })
    await expect(okta.getByText('Live', { exact: true })).toBeVisible()
    await expect(okta.getByText('Last fetched 12 min ago')).toBeVisible()
    await expect(okta.getByText(/Next read in 4[78] min/)).toBeVisible()
    await expect(okta.getByText('1 new: Perplexity')).toBeVisible()
    const aws = page.locator('.dv-src', { hasText: 'Prod AWS' })
    await expect(aws.getByText('Failing', { exact: true })).toBeVisible()
    await expect(aws.getByText(/InvalidClientTokenId/)).toBeVisible()
    await expect(page.getByText('Sources · 1 failing').first()).toBeVisible()
    await expect(page.locator('.dv-src', { hasText: 'Zscaler export' }).getByText('Upload an export to read it')).toBeVisible()
    await okta.getByRole('combobox', { name: 'How often to read Company Okta' }).click()
    await page.getByRole('option', { name: 'Daily' }).click()
    await expect.poll(() => patched).toEqual({ schedule_minutes: 1440 })
    const chooser = page.waitForEvent('filechooser')
    await page.locator('.dv-src', { hasText: 'Zscaler export' }).getByRole('button', { name: 'Upload logs' }).click()
    await (await chooser).setFiles({ name: 'proxy.csv', mimeType: 'text/csv', buffer: Buffer.from('time,user,url\n1,alice,https://chatgpt.com/\n') })
    await expect.poll(() => uploaded).toContain('chatgpt.com')
  })

  test('connect: suggests an unwatched area, previews, then connects on a schedule', async ({ page }) => {
    await page.goto('/discovery/connect')
    // Code and models is the first area nobody watches, so its first source is picked.
    await expect(page.getByRole('heading', { name: 'GitHub', level: 2 })).toBeVisible()
    await page.getByRole('button', { name: /^AWS/ }).click()
    await expect(page.getByText('bedrock:List*')).toBeVisible()
    await page.getByLabel('Access key ID').fill('AKIAEXAMPLE')
    await page.getByLabel('Secret access key').fill('secret-value')
    await page.getByRole('button', { name: 'Preview' }).click()
    await expect(page.locator('.dv-big')).toHaveText('9')
    await expect(page.getByText('2 Agent')).toBeVisible()
    expect(previewed).toMatchObject({ kind: 'aws', token: 'secret-value', config: { access_key_id: 'AKIAEXAMPLE' } })
    await page.getByRole('radio', { name: 'Hourly' }).click()
    await page.getByRole('button', { name: 'Connect and start watching' }).click()
    await page.waitForURL('**/discovery?view=sources')
    expect(created).toMatchObject({ kind: 'aws', name: 'AWS', token: 'secret-value', config: { access_key_id: 'AKIAEXAMPLE', schedule_minutes: 60 } })
    expect(JSON.stringify((created as { config: unknown }).config)).not.toContain('secret-value')
    expect(synced).toEqual(['i-new'])
  })
})
