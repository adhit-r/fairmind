import { expect, test, type Route } from '@playwright/test'

/**
 * Environmental governance workbench, exercised from the model evaluation flow.
 *
 * Backend calls are intercepted and fulfilled from fixtures, so the test runs
 * without credentials and never writes to a database. The fixtures mirror the
 * shapes the real API returns, verified against a running backend.
 *
 * What this pins down:
 *  - an ungoverned model offers registration instead of dead-ending,
 *  - a governed model renders the recommendation, confidence, matrix position
 *    and ENV control coverage,
 *  - the request the UI sends to the gate carries the reviewer's provenance
 *    and metrics,
 *  - a blocked sign-off surfaces the gate's own reason rather than a generic
 *    failure.
 */

const APP_URL = process.env.FAIRMIND_E2E_BASE_URL || 'http://localhost:1111'

/**
 * Matched on path, not host. The client resolves its base URL from
 * NEXT_PUBLIC_API_URL and falls back to the same-origin /api/proxy route, so a
 * host-specific pattern silently stops intercepting whenever that variable is
 * absent from the dev server's environment. Every backend call carries
 * /api/v1/ regardless of which base is in play.
 */
const API_GLOB = '**/api/v1/**'

const MODEL_ID = 'model-env-workbench'
const SYSTEM_ID = 'system-env-workbench'
const ASSESSMENT_ID = 'assessment-env-workbench'

const MODEL_FIXTURE = {
  model: {
    id: MODEL_ID,
    name: 'Claims Triage Model',
    description: 'Prioritises inbound insurance claims for manual review.',
    type: 'classification',
    status: 'active',
    fairness_score: 0.82,
    bias_score: 0.18,
  },
}

const CONTROLS_FIXTURE = {
  success: true,
  data: {
    controls: [
      { code: 'ENV-1', name: 'Assessment boundary', governance_test: 'Boundary declared.', optional: false },
      { code: 'ENV-2', name: 'Energy accounting', governance_test: 'Total kWh measured.', optional: false },
      { code: 'ENV-3', name: 'Dual carbon accounting', governance_test: 'Location and market carbon.', optional: false },
      { code: 'ENV-4', name: 'Efficiency metric', governance_test: 'Per functional unit.', optional: false },
      { code: 'ENV-5', name: 'Evidence confidence', governance_test: 'Provenance and uncertainty.', optional: false },
      { code: 'ENV-6', name: 'Mitigation and approval', governance_test: 'Mitigation or exception.', optional: false },
    ],
    coverage: null,
  },
}

/** A high-impact, measured-provenance assessment: conditional_go, still blocking. */
const ASSESSMENT_FIXTURE = {
  success: true,
  data: {
    systemId: SYSTEM_ID,
    empty: false,
    latest: {
      assessmentId: ASSESSMENT_ID,
      version: 1,
      createdAt: '2026-07-31T10:00:00Z',
      recommendation: 'conditional_go',
      impactTier: 'high',
      riskTier: 'high',
      confidenceScore: 0.93,
      confidenceBand: 'measured',
      provenanceClass: 'measured',
      reviewerState: 'draft',
      coverageRate: 0.8333,
      coverage: {
        'ENV-1': 'present',
        'ENV-2': 'present',
        'ENV-3': 'present',
        'ENV-4': 'present',
        'ENV-5': 'present',
        'ENV-6': 'missing',
      },
      blockers: [
        {
          code: 'environmental_mitigation_missing',
          severity: 'medium',
          message: 'conditional_go requires documented mitigation or a valid exception.',
        },
      ],
      result: {
        recommendation: 'conditional_go',
        impact_tier: 'high',
        confidence_score: 0.93,
        confidence_band: 'measured',
        mitigation_blocking: true,
        approval_blocking: true,
      },
    },
    versionTrail: [],
  },
}

type RouteOptions = {
  governed: boolean
  onAssess?: (payload: unknown) => void
  onApprove?: () => void
}

async function stubBackend(context: import('@playwright/test').BrowserContext, options: RouteOptions) {
  await context.addInitScript(() => {
    window.localStorage.setItem('access_token', 'fairmind-env-workbench-test')
    window.localStorage.setItem('selected_org_id', 'org-env-workbench-test')
  })

  await context.route(API_GLOB, async (route: Route) => {
    const request = route.request()
    const url = request.url()
    let status = 200
    let body: unknown = {}

    if (url.includes('/api/v1/auth/me')) {
      body = {
        id: 'user-env-workbench-test',
        email: 'reviewer@fairmind.local',
        full_name: 'Environmental Reviewer',
        role: 'admin',
        is_active: true,
      }
    } else if (url.includes('/api/v1/organizations')) {
      body = {
        organizations: [
          {
            id: 'org-env-workbench-test',
            name: 'FairMind Assurance',
            slug: 'fairmind-assurance',
            owner_id: 'user-env-workbench-test',
            created_at: '2026-07-18T00:00:00Z',
            role: 'admin',
          },
        ],
      }
    } else if (url.includes(`/api/v1/core/models/${MODEL_ID}`)) {
      body = MODEL_FIXTURE
    } else if (url.includes('/api/v1/core/datasets') || url.includes('/api/v1/datasets')) {
      body = { datasets: [] }
    } else if (url.includes(`/api/v1/ai-governance/models/${MODEL_ID}/system`)) {
      // The resolver returns governed=false rather than 404 for an ungoverned
      // model, so the UI can offer registration instead of erroring.
      body = options.governed
        ? { governed: true, modelId: MODEL_ID, system: { id: SYSTEM_ID, name: 'Claims Triage Model' } }
        : { governed: false, modelId: MODEL_ID, system: null }
    } else if (url.includes('/environmental-impact/') && url.includes('/approve')) {
      options.onApprove?.()
      status = 409
      body = {
        detail:
          'Environmental gate (conditional_go_blocked): conditional_go requires a documented mitigation with a target date before approval.',
      }
    } else if (url.includes('/api/v1/ai-governance/environment/assess')) {
      options.onAssess?.(request.postDataJSON())
      body = {
        success: true,
        evidence_id: 'evidence-env-workbench',
        assessment_id: ASSESSMENT_ID,
        version: 1,
        recommendation: 'conditional_go',
        impact_tier: 'high',
        evidence_confidence: 0.93,
        confidence_band: 'measured',
        requires_mitigation: true,
        mitigation_blocking: true,
        approval_blocking: true,
        coverage_rate: 0.8333,
        warnings: [],
      }
    } else if (url.includes('/environmental-impact')) {
      body = options.governed ? ASSESSMENT_FIXTURE : { success: true, data: { empty: true, latest: null, versionTrail: [] } }
    } else if (url.includes('/api/v1/environment/controls')) {
      body = CONTROLS_FIXTURE
    } else if (url.includes('/api/v1/ai-governance/workspaces')) {
      body = [{ id: 'workspace-env-workbench', name: 'Assurance workspace' }]
    }

    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
  })
}

test('an ungoverned model offers governance registration instead of dead-ending', async ({
  context,
  page,
}) => {
  await stubBackend(context, { governed: false })
  await page.goto(`${APP_URL}/models/${MODEL_ID}`, { waitUntil: 'domcontentloaded' })

  await expect(page.getByText('This model is not registered for governance.')).toBeVisible()
  await expect(page.getByRole('button', { name: /register for governance/i })).toBeEnabled()
})

test('a governed model shows its gate decision, confidence and control coverage', async ({
  context,
  page,
}) => {
  await stubBackend(context, { governed: true })
  await page.goto(`${APP_URL}/models/${MODEL_ID}`, { waitUntil: 'domcontentloaded' })

  // The release decision and the two dimensions that produced it.
  await expect(page.getByText('CONDITIONAL GO').first()).toBeVisible()
  await expect(page.getByText('0.93')).toBeVisible()
  await expect(page.getByText(/high.*impact/i).first()).toBeVisible()

  // Every ENV control is listed, and the failing one is visibly missing.
  for (const code of ['ENV-1', 'ENV-2', 'ENV-3', 'ENV-4', 'ENV-5', 'ENV-6']) {
    await expect(page.getByText(code, { exact: true })).toBeVisible()
  }
  await expect(page.getByText('missing').first()).toBeVisible()

  // The gate's blocker is surfaced to the reviewer, not swallowed.
  await expect(
    page.getByText(/conditional_go requires documented mitigation/i)
  ).toBeVisible()
})

test('the assessment form sends the reviewer provenance and metrics to the gate', async ({
  context,
  page,
}) => {
  const submitted: unknown[] = []
  await stubBackend(context, { governed: true, onAssess: (payload) => submitted.push(payload) })
  await page.goto(`${APP_URL}/models/${MODEL_ID}`, { waitUntil: 'domcontentloaded' })

  await page.getByRole('button', { name: /new assessment/i }).click()
  // The form defaults to the inference phase, which is tiered on
  // per-1000-request carbon, so that figure is required alongside the
  // supporting energy and total-carbon numbers.
  await page.getByLabel('Per 1000 requests (kg CO2e)').fill('0.004')
  await page.getByLabel('Total energy (kWh)').fill('40000')
  await page.getByLabel('Carbon, location-based (kg CO2e)').fill('20000')
  await page.getByLabel('Uncertainty (percent)').fill('8')
  await page.getByRole('button', { name: /evaluate against the gate/i }).click()

  await expect.poll(() => submitted.length).toBeGreaterThan(0)
  const payload = submitted[0] as {
    system_id: string
    assessment: { metrics: Record<string, number | null>; uncertainty_pct: number | null }
  }
  expect(payload.system_id).toBe(SYSTEM_ID)
  expect(payload.assessment.metrics.kg_co2e_per_1000_requests).toBe(0.004)
  expect(payload.assessment.metrics.total_kwh).toBe(40000)
  expect(payload.assessment.metrics.total_kg_co2e_location).toBe(20000)
  expect(payload.assessment.uncertainty_pct).toBe(8)
})

test('the phase-required metric is enforced before the gate is called', async ({ context, page }) => {
  const submitted: unknown[] = []
  await stubBackend(context, { governed: true, onAssess: (payload) => submitted.push(payload) })
  await page.goto(`${APP_URL}/models/${MODEL_ID}`, { waitUntil: 'domcontentloaded' })

  await page.getByRole('button', { name: /new assessment/i }).click()
  // Inference is tiered on per-1000-requests carbon; submitting without it
  // must be refused locally rather than sending an unusable assessment.
  await page.getByLabel('Total energy (kWh)').fill('12')
  await page.getByRole('button', { name: /evaluate against the gate/i }).click()

  await expect(page.getByText(/is tiered on/i)).toBeVisible()
  expect(submitted).toHaveLength(0)
})

test('a blocked sign-off surfaces the gate reason verbatim', async ({ context, page }) => {
  let approveCalled = false
  await stubBackend(context, { governed: true, onApprove: () => (approveCalled = true) })
  await page.goto(`${APP_URL}/models/${MODEL_ID}`, { waitUntil: 'domcontentloaded' })

  await page.getByPlaceholder('Reviewer name or identifier').fill('grc-lead')
  await page.getByRole('button', { name: /sign off/i }).click()

  await expect.poll(() => approveCalled).toBe(true)
  await expect(page.getByText(/requires a documented mitigation/i).first()).toBeVisible()
})
