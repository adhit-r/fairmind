import { expect, test, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

// Discovery overview, source monitoring and the connect flow; API calls are answered here, nothing reaches a database.
const BASE = '/api/v1/integrations'
const cors = { 'Access-Control-Allow-Origin': 'http://localhost:1111', 'Access-Control-Allow-Credentials': 'true', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS' }
const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, headers: cors, contentType: 'application/json', body: JSON.stringify(body) })
const minsAgo = (m: number) => new Date(Date.now() - m * 60_000).toISOString()
const minsAhead = (m: number) => new Date(Date.now() + m * 60_000).toISOString()
const run = (id: string, m: number, status: 'ok' | 'failed', found: number, created: number, names: string[] = [], error: string | null = null) => ({
  id, trigger: 'schedule', startedAt: minsAgo(m), finishedAt: minsAgo(m), status, found, created, updated: found - created, error, newNames: names,
})
const step = (key: string, title: string, call: string, toggleable: boolean, on = true) => ({ key, title, call, on, toggleable })
const ran = (key: string, found: number, created: number, samples: [string, string, boolean][]) => ({ key, found, created, off: false, samples: samples.map(([id, name, n]) => ({ id, name, new: n })) })
const integrations = [
  {
    id: 'i-okta', kind: 'okta', name: 'Company Okta', config: { domain: 'acme.okta.com', schedule_minutes: 60 }, hasToken: true,
    lastSyncedAt: minsAgo(12), lastSync: null, createdAt: minsAgo(3000), scheduleMinutes: 60, nextSyncAt: minsAhead(48),
    steps: [step('sso', 'AI apps in single sign-on', 'GET /api/v1/apps + /api/v1/logs', false)],
    recentRuns: [
      { ...run('r3', 12, 'ok', 4, 1, ['Perplexity']), steps: [ran('sso', 4, 1, [['okta:p', 'Perplexity', true], ['okta:a1', 'ChatGPT Enterprise', false]])] },
      run('r2', 72, 'ok', 3, 0),
      run('r1', 132, 'ok', 3, 3),
    ],
  },
  {
    id: 'i-aws', kind: 'aws', name: 'Prod AWS', config: { access_key_id: 'AKIA', schedule_minutes: 1440 }, hasToken: true,
    lastSyncedAt: minsAgo(1500), lastSync: null, createdAt: minsAgo(3000), scheduleMinutes: 1440, nextSyncAt: minsAgo(60),
    steps: [step('bedrock', 'Bedrock models', 'cloudwatch:ListMetrics', true), step('agents', 'Agents', 'bedrock-agent:ListAgents', true), step('sagemaker', 'SageMaker', 'sagemaker:ListEndpoints', true)],
    recentRuns: [
      run('a2', 30, 'failed', 0, 0, [], 'AWS rejected the credentials (InvalidClientTokenId)'),
      { ...run('a1', 1500, 'ok', 6, 6), steps: [ran('bedrock', 4, 4, [['b1', 'anthropic.claude-opus', true]]), ran('agents', 2, 2, [['aws:x', 'claims-agent', true]]), ran('sagemaker', 0, 0, [])] },
    ],
  },
  { id: 'i-logs', kind: 'proxy_logs', name: 'Zscaler export', config: {}, hasToken: false, lastSyncedAt: null, lastSync: null, createdAt: minsAgo(10), scheduleMinutes: 0, nextSyncAt: null, steps: [step('traffic', 'AI traffic in the log', 'Uploaded export', false)], recentRuns: [] },
]
const asset = (id: string, source: string, name: string, kind: string, status: string, metadata: Record<string, unknown>) => ({
  id, integrationId: 'i-okta', source, externalId: id, name, kind, metadata, suggestedTier: 'medium', suggestedStage: 'onboard', status, systemId: null, discoveredAt: minsAgo(12),
})
const discovered = [
  asset('okta:a1', 'okta', 'ChatGPT Enterprise', 'ai_service', 'new', { service: 'ChatGPT', vendor: 'OpenAI', distinct_users_30_days: 42 }),
  asset('aws:x', 'aws', 'claims-agent', 'agent', 'promoted', { service: 'Bedrock Agents' }),
]
// Since Shadow AI the waiting list is merged candidates, one row per system however many sources saw it.
const candidates = [
  { id: 'c-chatgpt', name: 'ChatGPT Enterprise', kind: 'ai_service', strength: 'strong', sources: ['okta'], sightings: 1, firstSeen: minsAgo(60), lastSeen: minsAgo(12), suggestedTier: 'medium', ownerCheck: null, owners: [] },
]
const candidateDetail = { ...candidates[0], members: [discovered[0]], checks: [], reach: [], tierReasons: [], frameworks: [], answers: null, mismatches: [], tools: [] }
const systems = [{ id: 'sys-existing', workspaceId: 'ws-1', name: 'Employee assistant', owner: 'owner@example.com', riskTier: 'medium', lifecycleStage: 'operate', metadata: {}, createdAt: minsAgo(3000) }]

test.describe('Discovery', () => {
  let created: Record<string, unknown> | null
  let patched: Record<string, unknown> | null
  let previewed: Record<string, unknown> | null
  let synced: string[]
  let uploaded: string | null
  let linked: Record<string, unknown> | null

  test.beforeEach(async ({ page }) => {
    created = patched = previewed = uploaded = linked = null
    synced = []
    await installGridFixtures(page)
    const handleApi = async (route: Route) => {
      const req = route.request()
      const path = new URL(req.url()).pathname.replace('/api/proxy', '')
      if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors })
      if (path === '/api/v1/auth/me') return json(route, { id: 'user-1', username: 'reviewer', email: 'reviewer@grid.test' })
      if (path === '/api/v1/organizations') return json(route, { organizations: [{ id: 'org-1', name: 'Grid org', slug: 'grid-org', owner_id: 'user-1', created_at: '2026-01-01T00:00:00Z', role: 'admin' }] })
      if (path === '/api/v1/shadow-ai') return json(route, { findings: [], resolved: [], map: { tools: [], teams: [], cells: {} }, coverage: { proxyLogs: false, okta: false, entra: false, gateway: false, mcpRegistry: false, people: 0, approvedTools: 0, ssoTools: 0 } })
      if (path === '/api/v1/ai-governance/systems') return json(route, systems)
      if (path === BASE && req.method() === 'GET') return json(route, integrations)
      if (path === BASE && req.method() === 'POST') {
        created = req.postDataJSON()
        return json(route, { ...integrations[0], id: 'i-new', ...created }, 201)
      }
      if (path === `${BASE}/preview`) {
        previewed = req.postDataJSON()
        return json(route, { found: 9, byKind: { llm_app: 7, agent: 2 }, sample: [{ name: 'anthropic.claude-opus', kind: 'llm_app', tier: 'medium' }, { name: 'claims-agent', kind: 'agent', tier: 'high' }] })
      }
      if (path === `${BASE}/i-aws` && req.method() === 'PATCH') {
        patched = req.postDataJSON()
        return json(route, integrations[1])
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
      if (path === '/api/v1/discovery/candidates') return json(route, candidates)
      if (path === '/api/v1/discovery/candidates/c-chatgpt' && req.method() === 'GET') return json(route, candidateDetail)
      if (path === '/api/v1/discovery/candidates/c-chatgpt/link' && req.method() === 'POST') {
        linked = req.postDataJSON()
        return json(route, { decision: 'link', systemId: 'sys-existing' })
      }
      return req.url().includes('/api/proxy/') ? route.fallback() : json(route, [])
    }
    await page.route('**/api/proxy/**', handleApi)
    await page.route('**/api/v1/**', handleApi)
  })

  test('overview shows watched and unwatched areas and what waits', async ({ page }) => {
    await page.goto('/discovery')
    const areas = page.getByRole('region', { name: 'Where AI can show up' })
    await expect(areas.getByRole('button', { name: /Sign-in and workplace.*1 found/ })).toBeVisible()
    await expect(areas.getByRole('button', { name: /MCP servers.*Not watched/ })).toBeVisible()
    await expect(page.getByText('1 registered')).toBeVisible()
    const waiting = page.getByRole('region', { name: 'Waiting for you' })
    await expect(waiting.getByText('ChatGPT Enterprise')).toBeVisible()
    await expect(waiting.getByText('No owner found')).toBeVisible()
    await areas.getByRole('button', { name: /Cloud/ }).click()
    await expect(waiting.getByText('Nothing waiting. Connectors on a schedule keep looking.')).toBeVisible()
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

  test('edit source updates its account and schedule while keeping the saved credential', async ({ page }) => {
    await page.goto('/discovery?view=sources')
    await page.locator('.dv-src', { hasText: 'Prod AWS' }).getByRole('link', { name: 'Edit' }).click()
    await expect(page.getByRole('heading', { name: 'Edit Prod AWS' })).toBeVisible()
    await expect(page.getByLabel('Access key ID')).toHaveValue('AKIA')
    await expect(page.getByText(/Leave blank to keep the saved credential/)).toBeVisible()
    await page.getByLabel('Access key ID').fill('AKIANEW')
    await page.getByLabel(/^Name/).fill('Production AI')
    await page.getByRole('radio', { name: 'Hourly' }).click()
    await page.getByRole('button', { name: 'Save changes' }).click()
    await page.waitForURL('**/discovery?view=sources')
    expect(patched).toMatchObject({ name: 'Production AI', config: { access_key_id: 'AKIANEW' }, schedule_minutes: 60, clear_token: false })
    expect((patched as Record<string, unknown>).token).toBeUndefined()
    expect(synced).toEqual(['i-aws'])
  })

  test('reviewer can link a separate sighting to an existing AI system', async ({ page }) => {
    await page.goto('/discovery?view=waiting')
    await expect(page.getByRole('heading', { name: 'ChatGPT Enterprise' })).toBeVisible()
    await page.getByRole('radio', { name: /Link to an existing AI system/ }).click()
    await expect(page.getByText(/Adds this sighting to Employee assistant/)).toBeVisible()
    await page.getByRole('button', { name: 'Link to AI system' }).click()
    await expect.poll(() => linked).toEqual({ system_id: 'sys-existing' })
  })

  test('flow shows each step with what it fetched, and saves a scope change', async ({ page }) => {
    await page.goto('/discovery?view=flow')
    const okta = page.locator('.fl-step', { hasText: 'AI apps in single sign-on' })
    await expect(okta.getByText('Perplexity')).toBeVisible()
    await expect(okta.locator('.fl-badge')).toHaveText('4')
    const bedrock = page.locator('.fl-step', { hasText: 'Bedrock models' })
    await expect(bedrock.getByText('Not reached · last good read')).toBeVisible()
    await expect(bedrock.getByText('anthropic.claude-opus')).toBeVisible()
    await page.locator('.fl-src', { hasText: 'Prod AWS' }).click()
    await expect(page.locator('.fl-insp').getByText(/InvalidClientTokenId/)).toBeVisible()
    await expect(okta.getByRole('switch')).toHaveCount(0) // a one-step source has nothing to switch off
    await page.getByRole('switch', { name: 'Stop reading SageMaker from Prod AWS' }).click()
    await expect(page.getByText('1 step off in 1 source')).toBeVisible()
    await page.getByRole('button', { name: 'Save scope' }).click()
    await expect.poll(() => patched).toEqual({ disabled_steps: ['sagemaker'] })
  })
})
