import { expect, test, type Page, type Route } from '@playwright/test'

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

const scopedRun = {
  id: 'run-1',
  organizationId: 'org-1',
  workspaceId: 'workspace-1',
  systemId: 'system-1',
  planId: 'plan-1',
  contractVersion: '2.0.0',
  trigger: 'manual',
  lifecyclePhase: 'pre_deploy',
  technicalStatus: 'leased',
  evidenceOutcome: 'passed_with_limitations',
  overallVerdict: 'review',
  layerVerdictsSchemaVersion: '1.0.0',
  layerVerdicts: { suites: {}, modalities: {}, components: {}, riskDimensions: {} },
  suiteExecutions: [{
    id: 'suite-execution-1',
    suiteVersionId: 'suite-version-1',
    ownerScope: 'organization',
    ordinal: 1,
    technicalStatus: 'succeeded',
    evidenceResultStatus: 'passed_with_limitations',
    admissionStatus: 'verified',
    reviewStatus: 'accepted',
    freshnessStatus: 'stale',
    recordedFreshnessStatus: 'current',
    freshnessContractVersion: '1.0.0',
    freshnessEvaluatedAt: '2026-08-30T00:00:00Z',
    freshnessEffectiveAt: '2026-08-29T00:00:00Z',
    expiringAt: '2026-09-30T00:00:00Z',
    freshnessReasonCodes: ['signing_key_revoked'],
    decisionEvidenceEligible: false,
    evidenceTrust: {
      sourceType: 'external_provider',
      issuerKey: 'issuer:assurance-lab',
      signingKeyId: 'signing-key-1',
      signerKeyId: 'signer-key-1',
      signerAlgorithm: 'Ed25519',
      effectiveExpiresAt: '2026-09-30T00:00:00Z',
      reviewedBy: 'reviewer-1',
      reviewedAt: '2026-08-30T00:00:00Z',
      admissionReasons: ['signature verified'],
    },
    limitations: ['Protected-group coverage is incomplete.'],
    failureCode: null,
    failureMessage: null,
  }],
  decisionEvidenceCurrentlyEligible: false,
  envelopeId: 'envelope-1',
  envelope: {
    schemaVersion: '2.0.0',
    envelopeId: 'envelope-1',
    runId: 'run-1',
    organizationId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    planId: 'plan-1',
    suites: [{
      suiteExecutionId: 'suite-execution-1',
      suiteVersionId: 'suite-version-1',
      ownerScope: 'organization',
    }],
  },
  envelopeHash: 'd'.repeat(64),
  verdictVersion: 1,
  requestedBy: 'user-1',
  startedAt: null,
  completedAt: null,
  failureCode: null,
  failureMessage: null,
  createdAt: '2026-08-30T00:00:00Z',
  updatedAt: '2026-08-30T00:00:00Z',
}

async function mockDashboardContext(
  page: Page,
  options: { run?: typeof scopedRun; v2Requests?: string[] } = {},
) {
  let resolveSystemResponse: (() => void) | undefined
  const systemResponseCompleted = new Promise<void>((resolve) => {
    resolveSystemResponse = resolve
  })

  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
    window.localStorage.setItem('fairmind:selected-ai-system', 'system-1')
  })
  await page.route('**/api/proxy/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/proxy', '')
    if (path.includes('/evaluation-v2/')) {
      options.v2Requests?.push(path)
      if (options.run && path.endsWith(`/runs/${options.run.id}`)) {
        return fulfillJson(route, options.run)
      }
      if (options.run && path.endsWith('/runs')) {
        return fulfillJson(route, [options.run])
      }
      return fulfillJson(route, [])
    }
    if (path === '/api/v1/auth/me') {
      return fulfillJson(route, {
        id: 'user-1',
        username: 'reviewer',
        email: 'reviewer@acme.test',
      })
    }
    if (path === '/api/v1/organizations') {
      return fulfillJson(route, {
        organizations: [{
          id: 'org-1',
          name: 'Acme Assurance',
          slug: 'acme-assurance',
          owner_id: 'user-1',
          created_at: '2026-08-28T08:00:00Z',
          role: 'admin',
          permissions: [],
        }],
      })
    }
    if (path === '/api/v1/ai-governance/systems') {
      await fulfillJson(route, [{
        id: 'system-1',
        workspaceId: 'workspace-1',
        name: 'Decisioning Agent',
        owner: 'agent-team@acme.test',
        riskTier: 'high',
        lifecycleStage: 'assess',
        readiness: 42,
        metadata: { source: 'registry' },
      }])
      resolveSystemResponse?.()
      return
    }
    return fulfillJson(route, [])
  })

  return { systemResponseCompleted }
}

test('disabled run child gate renders no preview data and makes no v2 request', async ({ page }) => {
  test.skip(
    process.env.NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED !== 'true'
      || process.env.NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED === 'true',
    'requires the dev server with the assurance master enabled and run child disabled',
  )

  const v2Requests: string[] = []
  const { systemResponseCompleted } = await mockDashboardContext(page, { v2Requests })

  await page.goto('/assurance/evaluations/run-1')

  await expect(page.getByRole('heading', { name: 'Assurance run preview disabled' })).toBeVisible()
  await systemResponseCompleted
  await expect(page.getByRole('region', { name: 'Selected AI system context' })).toContainText('Decisioning Agent')
  await page.waitForTimeout(250)
  expect(v2Requests).toEqual([])
})

test('enabled run child gate renders execution, evidence, and governance as separate axes', async ({ page }) => {
  test.skip(
    process.env.NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED !== 'true'
      || process.env.NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED !== 'true',
    'requires the dev server with both assurance run preview gates enabled',
  )

  await mockDashboardContext(page, { run: scopedRun })
  await page.goto('/assurance/evaluations/run-1')

  const panel = page.getByRole('region', { name: 'Evidence trust state' })
  await expect(panel.getByText('Execution status', { exact: true })).toBeVisible()
  await expect(panel.getByText('Leased', { exact: true })).toBeVisible()
  const evidenceAxis = panel.getByText('Evaluator evidence result', { exact: true }).locator('..')
  await expect(evidenceAxis).toBeVisible()
  await expect(evidenceAxis.getByText('Passed with limitations', { exact: true })).toBeVisible()
  const governanceAxis = panel.getByText('Governance verdict', { exact: true }).locator('..')
  await expect(governanceAxis).toBeVisible()
  await expect(governanceAxis.getByText('Review', { exact: true })).toBeVisible()

  const metadata = panel.getByRole('table', { name: 'Suite evidence trust metadata' })
  const suiteRow = metadata.getByRole('row').nth(1)
  await expect(metadata.getByRole('columnheader', { name: 'Source', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(1).getByText('external_provider', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Evidence signer', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(3).getByText('signer-key-1 (Ed25519)', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Effective expiry', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(4)).toContainText('Sep 30, 2026')
  await expect(metadata.getByRole('columnheader', { name: 'Admission reasons', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(6).getByText('signature verified', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Freshness / invalidation reasons', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(7).getByText('Signing key revoked', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Admission', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(13).getByText('Verified', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Freshness', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(14).getByText('Stale', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Review', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(15).getByText('Accepted', { exact: true })).toBeVisible()
  await expect(metadata.getByRole('columnheader', { name: 'Limitations', exact: true })).toBeVisible()
  await expect(suiteRow.getByRole('cell').nth(16).getByText('Protected-group coverage is incomplete.', { exact: true })).toBeVisible()
})
