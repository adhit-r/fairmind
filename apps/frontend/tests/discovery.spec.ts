import { expect, test, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

// Discovery overview, source monitoring and the connect flow; API calls are answered here, nothing reaches a database.
const BASE = '/api/v1/integrations'
const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
const fixtureTime = Date.parse('2026-11-23T09:00:00Z')
const minsAgo = (m: number) => new Date(fixtureTime - m * 60_000).toISOString()
const minsAhead = (m: number) => new Date(fixtureTime + m * 60_000).toISOString()
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
  id, integrationId: `i-${source}`, source, externalId: id, name, kind, metadata, suggestedTier: 'medium', suggestedStage: 'onboard', status, systemId: null, discoveredAt: minsAgo(12),
})
const discovered = [
  asset('okta:a1', 'okta', 'ChatGPT Enterprise', 'ai_service', 'new', { service: 'ChatGPT', vendor: 'OpenAI', distinct_users_30_days: 42 }),
  asset('aws:x', 'aws', 'claims-agent', 'agent', 'promoted', { service: 'Bedrock Agents' }),
]
// Since Shadow AI the waiting list is merged candidates, one row per system however many sources saw it.
const CANDIDATES = '/api/v1/discovery/candidates'
const candidates = [
  { id: 'c-chatgpt', name: 'ChatGPT Enterprise', kind: 'ai_service', strength: 'strong', sources: ['okta'], sightings: 1, firstSeen: minsAgo(60), lastSeen: minsAgo(12), suggestedTier: 'medium', ownerCheck: null, owners: [] },
]

test.describe('Discovery', () => {
  let created: Record<string, unknown> | null
  let patched: Record<string, unknown> | null
  let previewed: Record<string, unknown> | null
  let synced: string[]
  let uploaded: string | null

  test.beforeEach(async ({ page }) => {
    await page.clock.setFixedTime(fixtureTime)
    created = patched = previewed = uploaded = null
    synced = []
    await installGridFixtures(page)
    await page.route('**/api/v1/**', async (route) => {
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
      return route.fallback()
    })
  })

  test('opens the queue first and restores the exact sighting, filter and review on Back and reload', async ({ page, isMobile }) => {
    const other = { ...candidates[0], id: 'c-first', name: 'Unrelated model' }
    const merged = { ...candidates[0], sightings: 2, sources: ['okta', 'github'] }
    const canonical = asset(merged.id, 'github', merged.name, 'llm_app', 'new', { repo: 'review/chat-service' })
    await page.route(`**${BASE}/discovered?**`, (route) => json(route, [...discovered, canonical]))
    await page.route(`**${CANDIDATES}?**`, (route) => json(route, [other, merged]))
    const candidateDetail = {
      ...merged, members: [canonical, discovered[0]], checks: [], reach: [], tierReasons: [], frameworks: [], answers: null, mismatches: [], tools: [],
    }
    await page.route(`**${CANDIDATES}/**`, (route) => {
      const id = decodeURIComponent(new URL(route.request().url()).pathname.split('/').pop()!)
      return id === discovered[0].id || id === candidates[0].id ? json(route, candidateDetail) : json(route, { detail: 'Unknown candidate' }, 404)
    })
    await page.goto('/discovery')
    const queue = page.getByRole('region', { name: 'Waiting for you' })
    await expect(queue.getByRole('heading', { name: '2 candidates awaiting review', exact: true })).toBeVisible()
    const reviewCandidate = queue.getByRole('button', { name: 'Review ChatGPT Enterprise', exact: true })
    await expect(reviewCandidate.getByText('Review', { exact: true })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Inventory' }).getByText('2 candidates awaiting review', { exact: true })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Where AI can show up' })).toHaveCount(0)
    if (!isMobile) {
      const sourceSummary = page.getByRole('region', { name: 'Sources in the queue' })
      await sourceSummary.getByRole('button', { name: 'Filter by GitHub, 1 of 2 candidates' }).click()
      await expect(page).toHaveURL(/source=github/)
      await expect(queue.getByRole('button', { name: 'Review Unrelated model' })).toHaveCount(0)
      await expect(reviewCandidate).toBeVisible()
      await sourceSummary.getByRole('button', { name: 'Clear source filter' }).click()
      await expect(queue.getByRole('button', { name: 'Review Unrelated model' })).toBeVisible()
    }
    await page.getByRole('radio', { name: 'All sightings' }).click()
    await page.getByRole('row', { name: /42 people signed in/ }).getByRole('button', { name: 'Review it' }).click()
    await expect(page).toHaveURL(/c=okta%3Aa1/)
    const review = page.getByRole('region', { name: 'Candidate review', exact: true })
    await expect(review.getByRole('heading', { name: 'ChatGPT Enterprise' })).toBeVisible()
    await expect(review.getByText('Okta · Company Okta', { exact: true })).toBeVisible()
    await expect(review.getByText(/42 people signed in/)).toBeVisible()
    await expect(review.getByRole('heading', { name: 'Decision', exact: true })).toBeVisible()
    await page.reload()
    await expect(review.getByRole('heading', { name: 'ChatGPT Enterprise' })).toBeVisible()
    await page.goBack()
    await expect(page.getByRole('radio', { name: 'All sightings' })).toBeChecked()
    await expect(page.getByRole('row', { name: /42 people signed in/ })).toBeVisible()
  })

  test('phone review restores the source-filtered queue and fits the viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const items = Array.from({ length: 21 }, (_, i) => ({
      ...candidates[0], id: `candidate-${i}`, name: `System ${i}`, sources: i === 0 ? ['aws'] : ['okta'],
    }))
    await page.route(`**${CANDIDATES}?**`, (route) => json(route, items))
    await page.route(`**${CANDIDATES}/candidate-20?**`, (route) => json(route, {
      ...items[20], members: [discovered[0]], checks: [], reach: [], tierReasons: [], frameworks: [], answers: null, mismatches: [], tools: [],
    }))
    await page.goto('/discovery')
    const queue = page.getByRole('region', { name: 'Waiting for you' })
    const reviewCandidate = queue.getByRole('button', { name: 'Review System 20', exact: true })
    const source = page.getByRole('combobox', { name: 'Filter by source' })
    await source.selectOption('okta')
    await expect(page).toHaveURL(/source=okta/)
    await expect(queue.getByRole('button', { name: 'Review System 0', exact: true })).toHaveCount(0)
    await expect(reviewCandidate.getByText('Okta', { exact: true })).toBeVisible()
    await reviewCandidate.getByText('Review', { exact: true }).click()
    await expect(page).toHaveURL((url) => url.searchParams.get('c') === 'candidate-20' && url.searchParams.get('source') === 'okta')
    const selectedUrl = page.url()
    const review = page.getByRole('region', { name: 'Candidate review', exact: true })
    await expect(review.getByRole('heading', { name: 'System 20' })).toBeInViewport()
    await expect(queue).toHaveCount(0)
    await review.getByRole('link', { name: 'Source sightings' }).click()
    await expect(review.getByText(/42 people signed in/)).toBeInViewport()
    await review.getByRole('link', { name: 'Decision' }).click()
    await expect(review.getByRole('heading', { name: 'Decision' })).toBeInViewport()
    await expect(review.getByRole('heading', { name: 'Decision' })).toBeFocused()
    await expect(page).toHaveURL(selectedUrl)
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
    await review.getByRole('link', { name: 'Back to review queue' }).click()
    await expect(source).toHaveValue('okta')
    await expect(reviewCandidate).toBeInViewport()
    await expect(reviewCandidate).toBeFocused()
  })

  test('reloads the opened sighting after a split before allowing another candidate action', async ({ page }) => {
    const group = { ...candidates[0], id: 'group-A', name: 'Merged service', sightings: 2 }
    const member = { ...candidates[0], id: 'member-B', name: 'Separate service' }
    const a = { ...discovered[0], id: group.id, name: 'Sighting A' }
    const b = { ...discovered[0], id: member.id, name: 'Sighting B' }
    const facts = { checks: [], reach: [], tierReasons: [], frameworks: [], answers: null, mismatches: [], tools: [] }
    let split = false
    let asked = false
    let release!: () => void
    const nextDetail = new Promise<void>((resolve) => { release = resolve })
    const writes: string[] = []
    await page.route(`**${CANDIDATES}?**`, (route) => json(route, split ? [{ ...group, sightings: 1 }, member] : [group]))
    await page.route('**/api/v1/discovery/assets/member-B/split?**', (route) => {
      writes.push('member-B/split')
      expect(new URL(route.request().url()).searchParams.get('org_id')).toBe('org-1')
      split = true
      return json(route, { split: member.id })
    })
    await page.route(`**${CANDIDATES}/**`, async (route) => {
      const url = new URL(route.request().url())
      const endpoint = url.pathname.split('/candidates/')[1]
      expect(url.searchParams.get('org_id')).toBe('org-1')
      if (route.request().method() === 'POST') {
        writes.push(endpoint)
        if (endpoint === 'member-B/ask') {
          asked = true
          return json(route, { link: '/owner-check/brief-code', emailSent: false })
        }
        if (endpoint === 'member-B/ignore') return json(route, { status: 'ignored' })
        return json(route, { detail: 'Wrong candidate or action' }, 409)
      }
      expect(endpoint).toBe(member.id)
      if (split) {
        await nextDetail
        return json(route, { ...member, ...facts, members: [b] })
      }
      const ownerCheck = asked ? { email: 'reviewer@example.test', sentAt: minsAgo(1), answeredAt: null, expiresAt: minsAhead(100) } : null
      return json(route, { ...group, ...facts, members: [a, b], ownerCheck })
    })
    await page.goto('/discovery?view=waiting&c=member-B')
    const review = page.getByRole('region', { name: 'Candidate review', exact: true })
    await expect(review.getByRole('heading', { name: group.name })).toBeVisible()
    await expect(page.locator('.dv-side-queue button[aria-current="true"]')).toContainText(group.name)
    await review.getByRole('textbox', { name: 'Ask the owner' }).fill('reviewer@example.test')
    await review.getByRole('button', { name: 'Send the question' }).click()
    await expect(review.getByRole('button', { name: 'Send again' })).toBeVisible()
    await expect(review.getByRole('button', { name: 'Copy link' })).toBeVisible()
    await review.getByRole('radio', { name: 'Retire', exact: true }).check()
    await review.locator('.dv-src-row', { hasText: 'Sighting B' }).getByRole('button', { name: 'Split' }).click()
    await expect(review.getByRole('status', { name: 'Loading candidate evidence' })).toBeVisible()
    await expect(review.getByRole('button', { name: 'Ignore' })).toHaveCount(0)
    await expect(review.getByRole('heading', { name: 'Decision', exact: true })).toHaveCount(0)
    expect(writes).toEqual(['member-B/ask', 'member-B/split'])
    release()
    await expect(review.getByRole('heading', { name: member.name })).toBeVisible()
    await expect(review.getByRole('radio', { name: 'Approve', exact: true })).toBeChecked()
    await expect(review.getByRole('button', { name: 'Copy link' })).toHaveCount(0)
    await review.getByRole('button', { name: 'Ignore' }).click()
    await expect.poll(() => writes).toEqual(['member-B/ask', 'member-B/split', 'member-B/ignore'])
  })

  for (const action of ['ignore', 'decide'] as const) {
    test(`submits ${action} for the selected candidate in the selected organisation`, async ({ page }) => {
      let completed = false
      const selected = encodeURIComponent(discovered[0].id)
      await page.route(`**${CANDIDATES}?**`, (route) => json(route, completed ? [] : candidates))
      await page.route(`**${CANDIDATES}/**`, (route) => {
        const request = route.request()
        const url = new URL(request.url())
        expect(url.searchParams.get('org_id')).toBe('org-1')
        if (request.method() === 'GET') {
          expect(url.pathname.endsWith(`/candidates/${selected}`)).toBe(true)
          return json(route, {
            ...candidates[0], members: [discovered[0]], checks: [], reach: [], tierReasons: [], frameworks: [], answers: null, mismatches: [], tools: [],
          })
        }
        expect(request.method()).toBe('POST')
        expect(url.pathname.endsWith(`/candidates/${selected}/${action}`)).toBe(true)
        if (action === 'decide') expect(request.postDataJSON()).toMatchObject({ decision: 'approve', risk_tier: 'medium' })
        completed = true
        return json(route, action === 'ignore' ? { status: 'ignored' } : { decision: 'approve', systemId: 'from-discovery' })
      })
      await page.goto(`/discovery?view=waiting&c=${selected}`)
      const review = page.getByRole('region', { name: 'Candidate review', exact: true })
      if (action === 'decide') await review.getByRole('radio', { name: 'Approve', exact: true }).check()
      await review.getByRole('button', { name: action === 'ignore' ? 'Ignore' : 'Add to AI systems' }).click()
      if (action === 'decide') await expect(page).toHaveURL(/\/systems\/from-discovery$/)
      else await expect(page.getByRole('heading', { name: 'Nothing waiting for review' })).toBeVisible()
      expect(completed).toBe(true)
    })
  }

  test('keeps known candidates available while source counts are unavailable', async ({ page }) => {
    await page.route(`**${BASE}/discovered?**`, (route) => json(route, { detail: 'Source access denied' }, 403))
    await page.goto('/discovery')
    await expect(page.getByText('Source counts unavailable', { exact: false })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Waiting for you' }).getByText('ChatGPT Enterprise')).toBeVisible()
    await page.getByRole('radio', { name: 'All sightings', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Discovery sources could not load' })).toBeVisible()
  })

  test('only reports an empty queue after the queue read succeeds', async ({ page }) => {
    let broken = true
    let release!: () => void
    const firstRead = new Promise<void>((resolve) => { release = resolve })
    await page.route(`**${CANDIDATES}?**`, async (route) => {
      await firstRead
      return json(route, broken ? { detail: 'Queue unavailable' } : [], broken ? 403 : 200)
    })
    await page.goto('/discovery')
    await expect(page.getByRole('status', { name: 'Loading review queue' })).toBeVisible()
    await expect(page.getByRole('radio', { name: 'Awaiting review', exact: true })).toBeChecked()
    release()
    await expect(page.getByRole('heading', { name: 'Review queue could not load' })).toBeVisible()
    await expect(page.getByRole('radio', { name: 'Awaiting review', exact: true })).toBeChecked()
    await expect(page.getByText(/0 waiting for review/)).toHaveCount(0)
    broken = false
    await page.getByRole('button', { name: 'Retry queue' }).click()
    await expect(page.getByRole('region', { name: 'Where AI can show up' })).toBeVisible()
    await page.goto('/discovery?view=waiting')
    await expect(page.getByRole('heading', { name: 'Nothing waiting for review' })).toBeVisible()
    await page.goto('/discovery?show=ignored')
    await expect(page.getByText('Nothing ignored.')).toBeVisible()
  })

  test('distinguishes reviewed, missing, and unreadable exact candidates from a different waiting candidate', async ({ page }) => {
    const archived = { ...discovered[1], systemId: 'registered-claims' }
    await page.route(`**${BASE}/discovered?**`, (route) => json(route, [discovered[0], archived]))
    await page.route(`**${CANDIDATES}/**`, (route) => {
      const denied = new URL(route.request().url()).pathname.endsWith('denied')
      return json(route, { detail: denied ? 'Permission denied' : 'No longer waiting' }, denied ? 403 : 404)
    })
    await page.goto('/discovery?view=waiting&c=aws%3Ax')
    const review = page.getByRole('region', { name: 'Candidate review', exact: true })
    await expect(review.getByText('This sighting was registered.')).toBeVisible()
    await expect(review.getByRole('link', { name: 'Open registered system' })).toHaveAttribute('href', '/systems/registered-claims')
    await page.goto('/discovery?view=waiting&c=missing')
    await expect(review.getByText('Candidate is no longer in this queue')).toBeVisible()
    await page.goto('/discovery?c=denied')
    await expect(review.getByText('Candidate evidence could not load')).toBeVisible()
    await expect(review.getByRole('button', { name: 'Retry candidate' })).toBeVisible()
    await expect(review.getByRole('heading', { name: 'ChatGPT Enterprise' })).toHaveCount(0)
    for (const invalid of ['c=', 'c=c-chatgpt&c=denied']) {
      await page.goto(`/discovery?view=found&${invalid}`)
      await expect(page.getByRole('heading', { name: 'Candidate link is incomplete' })).toBeVisible()
      await expect(review).toHaveCount(0)
    }
  })

  test('explicit overview shows watched and unwatched areas and what waits', async ({ page }) => {
    await page.goto('/discovery?view=overview')
    const areas = page.getByRole('region', { name: 'Where AI can show up' })
    await expect(areas.getByRole('button', { name: /Sign-in and workplace.*1 found/ })).toBeVisible()
    await expect(areas.getByRole('button', { name: /MCP servers.*Not watched/ })).toBeVisible()
    await expect(page.getByText('1 registered')).toBeVisible()
    const waiting = page.getByRole('region', { name: 'Waiting for you' })
    await expect(waiting.getByText('ChatGPT Enterprise')).toBeVisible()
    await expect(waiting.getByText('No owner found')).toBeVisible()
    await areas.getByRole('button', { name: /Cloud/ }).click()
    await expect(waiting.getByText('No candidates are waiting in Cloud.')).toBeVisible()
  })

  test('sources view shows live state, failures and changes the schedule', async ({ page }) => {
    await page.goto('/discovery')
    const discoveryViews = page.getByRole('navigation', { name: 'Discovery view' })
    await discoveryViews.getByRole('button', { name: 'Sources · 1 failing' }).click()
    await expect(page).toHaveURL(/view=sources/)
    const okta = page.locator('.dv-src', { hasText: 'Company Okta' })
    await expect(okta.getByText('Live', { exact: true })).toBeVisible()
    await expect(okta.getByText('Last fetched 12 min ago')).toBeVisible()
    await expect(okta.getByText(/Next read in 4[78] min/)).toBeVisible()
    await expect(okta.getByText('1 new: Perplexity')).toBeVisible()
    const aws = page.locator('.dv-src', { hasText: 'Prod AWS' })
    await expect(aws.getByText('Failing', { exact: true })).toBeVisible()
    await expect(aws.getByText(/InvalidClientTokenId/)).toBeVisible()
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
