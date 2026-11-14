import { expect, test, type Route } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

// The discovery page with the newer sources; the browser's API calls are answered here, nothing reaches a database.
const BASE = '/api/v1/integrations'
const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
const at = '2026-11-14T09:00:00Z'
const integrations = [
  { id: 'i-okta', kind: 'okta', name: 'Company Okta', config: { domain: 'acme.okta.com' }, hasToken: true, lastSyncedAt: at, lastSync: { found: 1, created: 1, updated: 0, at }, createdAt: at },
  { id: 'i-logs', kind: 'proxy_logs', name: 'Zscaler export', config: {}, hasToken: false, lastSyncedAt: null, lastSync: null, createdAt: at },
]
const asset = (id: string, source: string, name: string, kind: string, metadata: Record<string, unknown>) => ({
  id, integrationId: 'i-okta', source, externalId: id, name, kind, metadata, suggestedTier: 'medium', suggestedStage: 'onboard', status: 'new', systemId: null, discoveredAt: at,
})
const discovered = [
  asset('okta:a1', 'okta', 'ChatGPT Enterprise', 'ai_service', { service: 'ChatGPT', vendor: 'OpenAI', distinct_users_30_days: 42 }),
  asset('acme/ops#mcp:postgres', 'github', 'postgres', 'mcp_server', { transport: 'stdio', command: 'npx pg-mcp', repo: 'acme/ops' }),
]

test.describe('Discovery sources', () => {
  let created: Record<string, unknown> | null
  let uploaded: string | null

  test.beforeEach(async ({ page }) => {
    created = null
    uploaded = null
    await installGridFixtures(page)
    await page.route('**/api/proxy/**', async (route) => {
      const req = route.request()
      const path = new URL(req.url()).pathname.replace('/api/proxy', '')
      if (path === BASE && req.method() === 'GET') return json(route, integrations)
      if (path === BASE && req.method() === 'POST') {
        created = req.postDataJSON()
        return json(route, { id: 'i-new', ...created, hasToken: true, lastSyncedAt: null, lastSync: null, createdAt: at }, 201)
      }
      if (path === `${BASE}/discovered`) return json(route, discovered)
      if (path === `${BASE}/i-logs/upload`) {
        uploaded = req.postDataJSON().text
        return json(route, { found: 2, created: 2, updated: 0, at })
      }
      return route.fallback()
    })
  })

  test('shows new source kinds and what they found', async ({ page }) => {
    await page.goto('/discovery')
    await expect(page.getByText('Company Okta')).toBeVisible()
    await expect(page.getByText('acme.okta.com')).toBeVisible()
    await expect(page.getByText('No logs uploaded yet')).toBeVisible()
    await expect(page.getByText('Uploaded log exports; the files are not kept')).toBeVisible()
    await expect(page.getByText('42 people signed in')).toBeVisible()
    await expect(page.getByText('MCP server', { exact: true })).toBeVisible()
    await expect(page.getByText(/stdio npx pg-mcp/)).toBeVisible()
  })

  test('uploads a proxy log export', async ({ page }) => {
    await page.goto('/discovery')
    const chooser = page.waitForEvent('filechooser')
    await page.getByRole('button', { name: 'Upload logs' }).click()
    await (await chooser).setFiles({ name: 'proxy.csv', mimeType: 'text/csv', buffer: Buffer.from('time,user,url\n1,alice,https://chatgpt.com/\n') })
    await expect.poll(() => uploaded).toContain('chatgpt.com')
  })

  test('connects AWS with its own fields and keeps the secret out of config', async ({ page }) => {
    await page.goto('/discovery')
    await page.getByRole('button', { name: 'Connect a source' }).first().click()
    const drawer = page.getByRole('dialog')
    await drawer.getByRole('combobox', { name: 'Source' }).click()
    await page.getByRole('option', { name: 'Cloud · AWS' }).click()
    await expect(drawer.getByText(/Bedrock models in use/)).toBeVisible()
    const add = drawer.getByRole('button', { name: 'Add connector' })
    await drawer.getByLabel('Name', { exact: false }).first().fill('Prod AWS')
    await expect(add).toBeDisabled()
    await drawer.getByLabel('Access key ID').fill('AKIAEXAMPLE')
    await drawer.getByLabel('Secret access key').fill('secret-value')
    await drawer.getByLabel('Regions').fill('us-east-1,eu-west-1')
    await add.click()
    await expect.poll(() => created).not.toBeNull()
    expect(created).toMatchObject({ kind: 'aws', name: 'Prod AWS', token: 'secret-value', config: { access_key_id: 'AKIAEXAMPLE', regions: 'us-east-1,eu-west-1' } })
    expect(JSON.stringify((created as { config: unknown }).config)).not.toContain('secret-value')
  })
})
