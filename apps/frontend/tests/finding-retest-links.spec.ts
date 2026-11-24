import { expect, test, type Page } from '@playwright/test'
import { installGridFixtures } from './grid-fixtures'

const evaluationId = 'EV-DAT-01'
const title = 'Population drift failed'
const original = 'original-failure'
const latest = 'latest-retest'
const earlier = 'earlier-retest'
const date = '2026-11-12T12:00:00Z'

function finding(id: string, systemId: string, metadata: Record<string, unknown>, source = 'fairmind.eval_engines') {
  return { id, systemId, source, metadata, title, severity: 'high', status: 'open', description: 'The observed distribution differed from the reference.', mitigation: '', timestamp: date }
}
const rows = [
  finding('finding-a', 'sys-a', { evaluationId, evidenceId: original, retestEvidenceId: latest, retestEvidenceIds: [earlier, latest] }),
  finding('finding-b', 'sys-b', { evaluationId, evidenceId: 'other-system-run' }),
  { ...finding('historical', 'sys-a', { evaluationId, evidenceId: 'old-failure' }), status: 'resolved' },
  finding('manual', 'sys-a', { evaluationId, evidenceId: original }, 'manual_assessment'),
  finding('missing-check', 'sys-a', { evidenceId: original }),
  finding('watch', 'sys-b', { latest_snapshot_id: 'snapshot-b' }, 'fairmind.watch'),
  finding('environment', 'sys-a', { assessment_id: 'assessment-a' }, 'environmental_impact'),
]
const records = [original, earlier, latest, 'later-unrelated', 'other-system-run'].map((id) => ({
  id, evaluationId, systemId: id === 'other-system-run' ? 'sys-b' : 'sys-a', systemName: id === 'other-system-run' ? 'Grid system B' : 'Grid system A',
  status: id === latest ? 'passed' : 'failed', summary: 'Measurement for ' + id, createdAt: date, detail: [], files: {}, metrics: {},
}))
const source = '/findings?system=sys-a&finding=finding-a'
const destination = (run: string) => `/compliance/evaluations/${evaluationId}?system=sys-a&run=${run}&finding=finding-a`

async function fixtures(page: Page) {
  await installGridFixtures(page)
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.split('/api/v1')[1]
    if (path === '/ai-governance/systems/sys-b') return route.fulfill({ json: { id: 'sys-b', workspaceId: 'ws-1', name: 'Grid system B', owner: 'owner-b', riskTier: 'low', lifecycleStage: 'govern', metadata: {}, createdAt: date, updatedAt: date } })
    if (path === '/ai-governance/evidence/sys-b/summary') return route.fulfill({ status: 404, json: { detail: 'No evidence summary' } })
    if (path === '/packs/ai-systems/sys-b/traces/summary') return route.fulfill({ json: null })
    if (path === '/ai-governance/approval/system/sys-b') return route.fulfill({ json: { request: null, decisions: [] } })
    if (path.startsWith('/ai-governance/systems/sys-b/')) return route.fulfill({ status: 404, json: { detail: 'No record' } })
    if (path === '/ai-governance/dashboard/risk') {
      const system = url.searchParams.get('system_id')
      const risks = rows.filter((row) => !system || row.systemId === system)
      return route.fulfill({ json: { risks, suggested: [], summary: { total: risks.length, open: risks.length - Number(risks.some((r) => r.status === 'resolved')), automated: risks.length, suggested: 0, bySeverity: { low: 0, medium: 0, high: risks.length, critical: 0 } } } })
    }
    if (path === '/ai-governance/remediation') return route.fulfill({ json: { tasks: [], summary: { activeTasks: 0 } } })
    if (path === `/packs/evaluations/${evaluationId}`) return route.fulfill({ json: {
      id: evaluationId, name: 'Population drift', measures: 'Check for distribution changes.', engine: 'Engine exists', runnable: true, installed: true,
      tests: [], pack: { id: 'data', name: 'Data quality' }, pattern: {}, results: null,
    } })
    if (path === `/packs/evaluations/${evaluationId}/engine`) return route.fulfill({ json: { id: evaluationId, slots: [], params: [], ways: [{ way: 'files', ready: true }], fit: 'intended' } })
    if (path === `/packs/evaluations/${evaluationId}/runs`) {
      const system = url.searchParams.get('system_id')
      // A newer, unrelated run is first; selected older records are deliberately outside this list.
      return route.fulfill({ json: records.filter((r) => r.systemId === system && r.id === 'later-unrelated') })
    }
    if (path.startsWith('/packs/evaluation-runs/')) {
      const run = records.find((r) => path.endsWith('/' + r.id))
      return run ? route.fulfill({ json: run }) : route.fulfill({ status: 404, json: { detail: 'Run unavailable' } })
    }
    return route.fallback()
  })
}

test('a finding keeps its original and each recorded retest across reload and browser Back', async ({ page }) => {
  await fixtures(page)
  await page.goto('/findings')
  const row = page.getByRole('row').filter({ hasText: 'Grid system A' }).filter({ hasText: 'Fairmind eval engines' }).first()
  await row.getByRole('button', { name: title }).click()
  await expect(page).toHaveURL(source)
  const drawer = page.getByRole('dialog', { name: 'Finding: ' + title })
  await expect(drawer.getByText('finding-a', { exact: true })).toBeVisible()
  await page.reload()
  for (const [label, id] of [['View original failed run', original], ['View recorded retest', latest], ['Retest 1', earlier]]) {
    if (id === earlier) await drawer.getByText('Earlier retests (1)').click()
    const link = drawer.getByRole('link', { name: label, exact: true })
    await expect(link).toHaveAttribute('href', destination(id))
    await link.click()
    await expect(page.getByText('Measurement for ' + id, { exact: true })).toBeVisible()
    await page.reload()
    await expect(page.getByText('Measurement for ' + id, { exact: true })).toBeVisible()
    await page.goBack()
    await expect(page).toHaveURL(id === earlier ? source + '&retests=all' : source)
    await expect(link).toBeVisible()
    await expect(drawer.getByText('finding-a', { exact: true })).toBeVisible()
    if (id === earlier) {
      await page.reload()
      await expect(link).toBeVisible()
    }
  }
})

test('unattributed and historical findings do not claim a retest and bad scopes stay unavailable', async ({ page }) => {
  await fixtures(page)
  for (const query of ['system=sys-b&finding=finding-a', 'system=sys-a&finding=missing', 'system=sys-a&system=sys-b&finding=finding-a', 'finding=finding-a']) {
    await page.goto('/findings?' + query)
    await expect(page.getByText('Finding unavailable', { exact: true })).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)
  }
  await page.goto('/findings?system=sys-a&finding=historical')
  await expect(page.getByText('No separate retest result is linked to this finding.')).toBeVisible()
  await expect(page.getByText('Prepare a retest', { exact: true })).toHaveCount(0)
  await page.goto('/findings?system=sys-a&finding=manual')
  await expect(page.getByText('No originating check is recorded for a retest.')).toBeVisible()
  await expect(page.getByRole('link', { name: 'View original failed run' })).toHaveCount(0)
  await page.goto('/findings?system=sys-a&finding=missing-check')
  await expect(page.getByRole('link', { name: 'View original evidence' })).toHaveAttribute('href', '/evidence?system=sys-a&evidence=original-failure')
  await expect(page.getByRole('link', { name: 'Prepare a retest' })).toHaveCount(0)
  await page.goto('/findings?system=sys-b&finding=finding-b')
  await expect(page.getByRole('link', { name: 'Prepare a retest' })).toHaveAttribute('href', `/compliance/evaluations/${evaluationId}?system=sys-b&finding=finding-b`)
})

test('a copied result link rejects a different finding, check, system or run even when the titles match', async ({ page }) => {
  await fixtures(page)
  for (const target of [
    destination('later-unrelated'), destination('other-system-run'),
    destination(original).replace('finding-a', 'manual'),
    destination(original).replace('sys-a', 'sys-b'),
    destination(original).replace(evaluationId, 'EV-DAT-02'),
  ]) {
    await page.goto(target)
    await expect(page.getByText('This finding does not identify that check or run on this system.')).toBeVisible()
    await expect(page.getByText(/^Measurement for /)).toHaveCount(0)
  }
  await page.route('**/api/v1/packs/evaluation-runs/**', (route) =>
    route.fulfill({ json: { ...records[0], systemId: 'sys-b', summary: 'Measurement for a different system' } }))
  await page.goto(destination(original))
  await expect(page.getByText(/Recorded result unavailable for this system and check/)).toBeVisible()
  await expect(page.getByText('Measurement for a different system')).toHaveCount(0)
})

test('monitoring and environmental findings offer their own scoped forms', async ({ page }) => {
  await fixtures(page)
  await page.goto('/findings?system=sys-b&finding=watch')
  const drawer = page.getByRole('dialog')
  await expect(drawer.getByRole('link', { name: 'View triggering monitoring snapshot' })).toHaveAttribute('href', '/evidence?system=sys-b&evidence=snapshot-b')
  await expect(drawer.getByRole('link', { name: 'Prepare a monitoring snapshot' })).toHaveAttribute('href', '/systems/sys-b?finding=watch#operate')
  await drawer.getByRole('link', { name: 'Prepare a monitoring snapshot' }).click()
  await expect(page.getByRole('dialog', { name: 'Record a monitoring snapshot' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Back to finding' })).toHaveAttribute('href', '/findings?system=sys-b&finding=watch')
  await page.reload()
  await page.getByRole('link', { name: 'Back to finding' }).click()
  await expect(drawer.getByRole('link', { name: 'View triggering monitoring snapshot' })).toBeVisible()
  await page.goto('/findings?system=sys-a&finding=environment')
  await drawer.getByRole('link', { name: 'Prepare an environmental assessment' }).click()
  await expect(page.getByRole('dialog', { name: 'Start an assessment on Grid system A' })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('dialog', { name: 'Start an assessment on Grid system A' })).toBeVisible()
  await page.goBack()
  await expect(drawer.getByText(/Original assessment ID: assessment-a/)).toBeVisible()
  await page.goto('/environment?system=sys-a&action=assess&finding=watch')
  await expect(page.getByText('Retest unavailable', { exact: true })).toBeVisible()
  await page.goto('/systems/sys-b?finding=environment#operate')
  await expect(page.getByText('Retest unavailable', { exact: true })).toBeVisible()
})

test('a retired system keeps its source record and cannot prepare a finding retest', async ({ page }) => {
  await fixtures(page)
  await page.route('**/api/v1/ai-governance/systems?**', (route) => route.fulfill({ json: [{
    id: 'sys-b', workspaceId: 'ws-1', name: 'Retired system', owner: 'reviewer', riskTier: 'low', lifecycleStage: 'retired',
    metadata: {}, createdAt: date, updatedAt: date,
  }] }))
  await page.goto('/findings?system=sys-b&finding=finding-b')
  const drawer = page.getByRole('dialog')
  await expect(drawer.getByText('This system is retired. Only recorded results are available.')).toBeVisible()
  await expect(drawer.getByRole('link', { name: 'View original failed run' })).toBeVisible()
  await expect(drawer.getByRole('link', { name: 'Prepare a retest' })).toHaveCount(0)
})
