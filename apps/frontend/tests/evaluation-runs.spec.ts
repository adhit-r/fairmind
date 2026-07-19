import { expect, test, type Page, type Route } from '@playwright/test'

const organization = {
  id: 'org-1',
  name: 'Acme Assurance',
  slug: 'acme-assurance',
  owner_id: 'user-1',
  created_at: '2026-07-19T08:00:00Z',
  role: 'admin',
  permissions: ['model:read', 'model:write'],
}

const governedSystem = {
  id: 'system-1',
  workspaceId: 'workspace-1',
  name: 'Decisioning Agent',
  owner: 'agent-team@acme.test',
  riskTier: 'high',
  lifecycleStage: 'assess',
  readiness: 42,
  metadata: { source: 'registry' },
}

const basePlan = {
  id: 'plan-external',
  orgId: 'org-1',
  workspaceId: 'workspace-1',
  systemId: 'system-1',
  name: 'Agent release assurance',
  targetKind: 'agent',
  lifecyclePhases: ['pre_deploy', 'realtime'],
  executionDepth: 'hybrid',
  enforcementMode: 'human_approval',
  deliveryMode: 'external_provider',
  suiteRefs: ['fairmind/agent-safety@2026.07'],
  status: 'active',
  createdBy: 'user-1',
  updatedBy: 'user-1',
  createdAt: '2026-07-19T08:10:00Z',
  updatedAt: '2026-07-19T08:15:00Z',
} as const

const awaitingRun = {
  id: 'run-awaiting',
  orgId: 'org-1',
  workspaceId: 'workspace-1',
  systemId: 'system-1',
  planId: 'plan-external',
  trigger: 'manual',
  technicalStatus: 'awaiting_evidence',
  overallVerdict: 'insufficient',
  layerVerdicts: {},
  linkedEvidenceRunId: null,
  linkedPassportRevisionId: null,
  linkedBy: null,
  linkedAt: null,
  requestedBy: 'user-1',
  startedAt: null,
  completedAt: null,
  failureCode: null,
  failureMessage: null,
  createdAt: '2026-07-19T08:20:00Z',
  updatedAt: '2026-07-19T08:20:00Z',
} as const

const reviewedRun = {
  ...awaitingRun,
  id: 'run-reviewed',
  technicalStatus: 'succeeded',
  overallVerdict: 'review',
  layerVerdicts: {
    components: { model: 'review', tools: 'conditional' },
    dimensions: { security: 'conditional', governance: 'review' },
  },
  linkedEvidenceRunId: 'evidence-run-418',
  linkedPassportRevisionId: 'passport-revision-7',
  linkedBy: 'reviewer-1',
  linkedAt: '2026-07-19T08:30:00Z',
  startedAt: '2026-07-19T08:21:00Z',
  completedAt: '2026-07-19T08:29:00Z',
  createdAt: '2026-07-19T08:21:00Z',
  updatedAt: '2026-07-19T08:30:00Z',
} as const

type MockOptions = {
  organizations?: Array<Record<string, unknown>>
  systems?: Array<Record<string, unknown>>
  plans?: Array<Record<string, unknown>>
  runs?: Array<Record<string, unknown>>
  detailRun?: Record<string, unknown>
  listDelayMs?: number
  listError?: boolean
  createRunError?: boolean
  portraitFailure?: boolean
  secondaryScope?: {
    systemId: string
    plans: Array<Record<string, unknown>>
    runs?: Array<Record<string, unknown>>
    listDelayMs?: number
  }
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

async function mockEvaluationWorkbench(page: Page, options: MockOptions = {}) {
  let plans = structuredClone(options.plans ?? [])
  let runs = structuredClone(options.runs ?? [])
  const evaluationRequestPaths: string[] = []
  const evaluationMutationPaths: string[] = []

  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
    window.localStorage.setItem('fairmind:selected-ai-system', 'system-1')
  })

  if (options.portraitFailure !== false) {
    await page.route(/https:\/\/ui\.shadcn\.com\/avatars\/02\.png(?:\?.*)?$/, (route) => route.abort('failed'))
  }
  await page.route('**/api/proxy/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace('/api/proxy', '')

    if (path === '/api/v1/auth/me') {
      return fulfillJson(route, { id: 'user-1', username: 'reviewer', email: 'reviewer@acme.test' })
    }
    if (path === '/api/v1/organizations') {
      return fulfillJson(route, { organizations: options.organizations ?? [organization] })
    }
    if (path === '/api/v1/ai-governance/systems') {
      return fulfillJson(route, options.systems ?? [governedSystem])
    }

    if (/\/evaluation-(?:plans|runs)(?:\/|$)/.test(path)) {
      evaluationRequestPaths.push(path)
      if (request.method() !== 'GET') evaluationMutationPaths.push(path)
    }

    const evaluationPrefix = '/api/v1/ai-governance/organizations/org-1/systems/system-1'
    const secondaryPrefix = options.secondaryScope
      ? `/api/v1/ai-governance/organizations/org-1/systems/${options.secondaryScope.systemId}`
      : null
    if (secondaryPrefix && path.startsWith(secondaryPrefix)) {
      if (options.secondaryScope?.listDelayMs && request.method() === 'GET' && (
        path === `${secondaryPrefix}/evaluation-plans`
        || path === `${secondaryPrefix}/evaluation-runs`
      )) {
        await new Promise((resolve) => setTimeout(resolve, options.secondaryScope?.listDelayMs))
      }
      if (path === `${secondaryPrefix}/evaluation-plans` && request.method() === 'GET') {
        return fulfillJson(route, options.secondaryScope?.plans ?? [])
      }
      if (path === `${secondaryPrefix}/evaluation-runs` && request.method() === 'GET') {
        return fulfillJson(route, options.secondaryScope?.runs ?? [])
      }
      const secondaryPreflight = path.match(/\/evaluation-plans\/([^/]+)\/preflight$/)
      if (secondaryPreflight && request.method() === 'GET') {
        return fulfillJson(route, {
          planId: secondaryPreflight[1],
          canPrepareRun: true,
          fairmindExecutionAvailable: false,
          code: 'evidence_link_required',
          message: 'Prepare the run, then link evidence from the configured provider.',
          nextAction: 'Link an exact Evidence Passport revision after external execution.',
        })
      }
      return fulfillJson(route, [])
    }
    if (!path.startsWith(evaluationPrefix)) {
      return fulfillJson(route, [])
    }

    if (options.listDelayMs && request.method() === 'GET' && (
      path === `${evaluationPrefix}/evaluation-plans`
      || path === `${evaluationPrefix}/evaluation-runs`
    )) {
      await new Promise((resolve) => setTimeout(resolve, options.listDelayMs))
    }

    if (path === `${evaluationPrefix}/evaluation-plans`) {
      if (request.method() === 'POST') {
        const input = request.postDataJSON()
        const created = {
          id: `plan-${plans.length + 1}`,
          orgId: 'org-1',
          workspaceId: 'workspace-1',
          systemId: 'system-1',
          ...input,
          status: 'draft',
          createdBy: 'user-1',
          updatedBy: 'user-1',
          createdAt: '2026-07-19T09:00:00Z',
          updatedAt: '2026-07-19T09:00:00Z',
        }
        plans = [created, ...plans]
        return fulfillJson(route, created, 201)
      }
      if (options.listError) {
        return fulfillJson(route, { detail: 'Evaluation plan service unavailable' }, 422)
      }
      return fulfillJson(route, plans)
    }

    if (path === `${evaluationPrefix}/evaluation-runs` && request.method() === 'GET') {
      if (options.listError) {
        return fulfillJson(route, { detail: 'Evaluation run service unavailable' }, 422)
      }
      return fulfillJson(route, runs)
    }

    const activateMatch = path.match(/\/evaluation-plans\/([^/]+)\/activate$/)
    if (activateMatch && request.method() === 'POST') {
      const planId = activateMatch[1]
      let activated: Record<string, unknown> | undefined
      plans = plans.map((plan) => {
        if (plan.id !== planId) return plan
        activated = { ...plan, status: 'active', updatedAt: '2026-07-19T09:05:00Z' }
        return activated
      })
      return fulfillJson(route, activated)
    }

    const preflightMatch = path.match(/\/evaluation-plans\/([^/]+)\/preflight$/)
    if (preflightMatch && request.method() === 'GET') {
      const plan = plans.find((candidate) => candidate.id === preflightMatch[1])
      const isWorker = plan?.deliveryMode === 'fairmind_worker'
      return fulfillJson(route, {
        planId: preflightMatch[1],
        canPrepareRun: !isWorker,
        fairmindExecutionAvailable: false,
        code: isWorker ? 'executor_unavailable' : 'evidence_link_required',
        message: isWorker
          ? 'FairMind execution workers are unavailable in this release.'
          : 'Prepare the run, then link evidence from the configured provider.',
        nextAction: isWorker
          ? 'Choose an external provider or imported report delivery mode.'
          : 'Link an exact Evidence Passport revision after external execution.',
      })
    }

    const createRunMatch = path.match(/\/evaluation-plans\/([^/]+)\/runs$/)
    if (createRunMatch && request.method() === 'POST') {
      if (options.createRunError) {
        return fulfillJson(route, {
          detail: {
            code: 'executor_unavailable',
            message: 'Run preparation is temporarily blocked.',
            nextAction: 'Use an imported report or retry after the executor is connected.',
          },
        }, 409)
      }
      const created = {
        ...awaitingRun,
        id: `run-prepared-${runs.length + 1}`,
        planId: createRunMatch[1],
        trigger: request.postDataJSON().trigger,
        createdAt: '2026-07-19T09:10:00Z',
        updatedAt: '2026-07-19T09:10:00Z',
      }
      runs = [created, ...runs]
      return fulfillJson(route, created, 201)
    }

    const detailMatch = path.match(/\/evaluation-runs\/([^/]+)$/)
    if (detailMatch && request.method() === 'GET') {
      const detail = options.detailRun ?? runs.find((run) => run.id === detailMatch[1])
      return detail
        ? fulfillJson(route, detail)
        : fulfillJson(route, { detail: 'Evaluation run not found' }, 404)
    }

    return fulfillJson(route, [])
  })

  return {
    getEvaluationRequestCount: () => evaluationRequestPaths.length,
    getEvaluationRequestPaths: () => [...evaluationRequestPaths],
    getEvaluationMutationPaths: () => [...evaluationMutationPaths],
  }
}

test('keeps Evaluation Runs inside the original shell with framed, labelled identity and controls', async ({ page }) => {
  await mockEvaluationWorkbench(page)
  await page.goto('/tests')

  await expect(page.getByRole('banner')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Evaluation Runs', level: 1 })).toBeVisible()
  await expect(page.getByText('Acme Assurance', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Decisioning Agent', exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Evaluation Runs' })).toBeVisible()

  const navigationToggle = page.getByRole('button', { name: 'Toggle navigation' })
  const toggleBox = await navigationToggle.boundingBox()
  expect(toggleBox?.width).toBeGreaterThanOrEqual(44)
  expect(toggleBox?.height).toBeGreaterThanOrEqual(44)
  await navigationToggle.focus()
  await expect(navigationToggle).toBeFocused()
  expect(await navigationToggle.evaluate((element) => getComputedStyle(element).outlineStyle)).not.toBe('none')

  const search = page.getByRole('searchbox')
  await search.focus()
  await expect(search).toBeFocused()
  expect(await search.evaluate((element) => element.matches(':focus-visible'))).toBe(true)
  await expect(search).toHaveCSS('outline-color', 'rgb(15, 20, 18)')
  await expect(search).toHaveCSS('outline-style', 'solid')
  await expect(search).toHaveCSS('outline-width', '2px')

  await expect(page.getByLabel('User Name profile image unavailable; showing initials UN').first()).toBeVisible()
  await expect(page.locator('[data-framed-icon="true"]').first()).toBeVisible()
  await expect(page.getByText('Test History', { exact: true })).toHaveCount(0)
  await expect(page.getByText('Total Tests', { exact: true })).toHaveCount(0)
  await expect(page.getByText('Passed', { exact: true })).toHaveCount(0)

  await page.screenshot({ path: '/tmp/fairmind-evaluation-runs-fallback.png', fullPage: true })

  await navigationToggle.click()
  await page.waitForTimeout(250)
  const collapsedRunLink = page.getByRole('link', { name: 'Evaluation Runs' })
  const collapsedLinkBox = await collapsedRunLink.boundingBox()
  expect(collapsedLinkBox?.width).toBeGreaterThanOrEqual(44)
  expect(collapsedLinkBox?.height).toBeGreaterThanOrEqual(44)
  await expect(page.getByRole('button', { name: 'User Name profile' })).toBeVisible()
})

test('keeps the identity visible and the workbench usable in the mobile shell', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await mockEvaluationWorkbench(page, { plans: [basePlan], runs: [awaitingRun], portraitFailure: false })
  await page.goto('/tests')

  await expect(page.getByRole('heading', { name: 'Evaluation Runs', level: 1 })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Open user menu for User Name' })).toBeVisible()
  const layout = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
  }))
  expect(layout.documentScrollWidth).toBeLessThanOrEqual(layout.innerWidth)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: '/tmp/fairmind-evaluation-runs-mobile.png', fullPage: true })

  await page.getByRole('button', { name: 'Toggle navigation' }).click()
  await expect(page.getByRole('link', { name: 'Evaluation Runs' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'User Name profile' })).toBeVisible()
})

test('treats the synthetic fallback system as missing and makes no evaluation request', async ({ page }) => {
  const mocks = await mockEvaluationWorkbench(page, { systems: [] })
  await page.goto('/tests')

  await expect(page.getByRole('heading', { name: 'Choose an AI system' })).toBeVisible()
  await expect(page.getByText('Acme Pricing Lab', { exact: true })).toHaveCount(0)
  await page.waitForTimeout(300)
  expect(mocks.getEvaluationRequestCount()).toBe(0)
  expect(mocks.getEvaluationRequestPaths()).toEqual([])
})

test('masks old-system plans and actions before delayed new-system evaluation lists resolve', async ({ page }) => {
  const secondSystem = {
    ...governedSystem,
    id: 'system-2',
    name: 'Claims Review Agent',
    workspaceId: 'workspace-2',
  }
  const secondPlan = {
    ...basePlan,
    id: 'plan-system-2',
    systemId: 'system-2',
    workspaceId: 'workspace-2',
    name: 'Claims release assurance',
  }
  const mocks = await mockEvaluationWorkbench(page, {
    systems: [governedSystem, secondSystem],
    plans: [basePlan],
    secondaryScope: {
      systemId: 'system-2',
      plans: [secondPlan],
      listDelayMs: 800,
    },
  })
  await page.goto('/tests')
  await expect(page.getByLabel('Selected plan')).toContainText(basePlan.name)
  await expect(page.getByRole('button', { name: 'Prepare evidence run' })).toBeVisible()

  await page.getByRole('combobox', { name: 'System scope' }).click()
  await page.getByRole('option', { name: secondSystem.name }).click()

  await expect(page.getByText(basePlan.name, { exact: true })).toHaveCount(0, { timeout: 400 })
  await expect(page.getByRole('button', { name: 'Prepare evidence run' })).toHaveCount(0, { timeout: 400 })
  expect(mocks.getEvaluationMutationPaths().filter((path) => path.includes('/systems/system-1/'))).toEqual([])
  await expect(page.getByLabel('Selected plan')).toContainText(secondPlan.name)
})

test('requires an organization before rendering the scoped workbench', async ({ page }) => {
  const mocks = await mockEvaluationWorkbench(page, { organizations: [] })
  await page.goto('/tests')

  await expect(page.getByRole('heading', { name: 'Choose an organization' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Evaluation plan' })).toHaveCount(0)
  await page.waitForTimeout(300)
  expect(mocks.getEvaluationRequestPaths()).toEqual([])
})

test('creates a version-pinned plan from the compact empty-state form', async ({ page }) => {
  await mockEvaluationWorkbench(page)
  await page.goto('/tests')

  const form = page.getByRole('form', { name: 'Create evaluation plan' })
  await expect(form.getByLabel('Plan name')).toBeVisible()
  await expect(form.getByLabel('Target kind')).toBeVisible()
  await expect(form.getByRole('group', { name: 'Lifecycle phases' })).toBeVisible()
  await expect(form.getByLabel('Execution depth')).toBeVisible()
  await expect(form.getByLabel('Enforcement mode')).toBeVisible()
  await expect(form.getByLabel('Delivery mode')).toBeVisible()
  await expect(form.getByLabel('Versioned suite references')).toBeVisible()

  await form.getByLabel('Plan name').fill('Image generation release gate')
  await form.getByLabel('Target kind').selectOption('image_generator')
  await form.getByLabel('Realtime').check()
  await form.getByLabel('Delivery mode').selectOption('imported_report')
  await form.getByLabel('Versioned suite references').fill('fairmind/image-safety@2026.07')
  await form.getByRole('button', { name: 'Create evaluation plan' }).click()

  await expect(page.getByLabel('Selected plan')).toHaveValue('plan-1')
  await expect(page.getByText('Draft', { exact: true })).toBeVisible()
})

test('blocks unavailable FairMind workers with an explicit next action', async ({ page }) => {
  const workerPlan = { ...basePlan, id: 'plan-worker', deliveryMode: 'fairmind_worker' }
  await mockEvaluationWorkbench(page, { plans: [workerPlan] })
  await page.goto('/tests')

  const preflight = page.getByRole('region', { name: 'Evaluation preflight' })
  await expect(preflight.getByText('Executor unavailable', { exact: true })).toBeVisible()
  await expect(preflight.getByText('FairMind execution: unavailable', { exact: true })).toBeVisible()
  await expect(preflight).toContainText('Choose an external provider or imported report delivery mode.')
  await expect(preflight.getByRole('button', { name: 'Prepare evidence run' })).toBeDisabled()
})

test('requires an active plan even when delivery preflight can prepare evidence', async ({ page }) => {
  const draftPlan = { ...basePlan, id: 'plan-draft', status: 'draft' }
  await mockEvaluationWorkbench(page, { plans: [draftPlan] })
  await page.goto('/tests')

  const preflight = page.getByRole('region', { name: 'Evaluation preflight' })
  await expect(preflight.getByText('Run preparation: blocked', { exact: true })).toBeVisible()
  await expect(preflight.getByText('Run preparation: allowed', { exact: true })).toHaveCount(0)
  await expect(preflight).toContainText('Activate this plan version')
  await expect(preflight.getByRole('button', { name: 'Prepare evidence run' })).toBeDisabled()

  await page.unroute('**/api/proxy/**')
  const archivedPlan = { ...basePlan, id: 'plan-archived', status: 'archived' }
  await mockEvaluationWorkbench(page, { plans: [archivedPlan] })
  await page.reload()

  const archivedPreflight = page.getByRole('region', { name: 'Evaluation preflight' })
  await expect(archivedPreflight.getByText('Run preparation: blocked', { exact: true })).toBeVisible()
  await expect(archivedPreflight.getByText('Run preparation: allowed', { exact: true })).toHaveCount(0)
  await expect(archivedPreflight).toContainText('Create a new plan version')
  await expect(archivedPreflight.getByRole('button', { name: 'Prepare evidence run' })).toBeDisabled()
})

test('prepares external evidence runs without conflating technical status and governance verdict', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await mockEvaluationWorkbench(page, {
    plans: [basePlan],
    runs: [reviewedRun, awaitingRun],
    portraitFailure: false,
  })
  await page.goto('/tests')

  const preflight = page.getByRole('region', { name: 'Evaluation preflight' })
  await expect(preflight.getByText('Evidence link required', { exact: true })).toBeVisible()
  await expect(preflight.getByText('FairMind execution: unavailable', { exact: true })).toBeVisible()
  await expect(preflight.getByText('Run preparation: allowed', { exact: true })).toBeVisible()
  await preflight.getByRole('button', { name: 'Prepare evidence run' }).click()

  const table = page.getByRole('table', { name: 'Recent evaluation runs' })
  await expect(table.getByRole('columnheader', { name: 'Technical status' })).toBeVisible()
  await expect(table.getByRole('columnheader', { name: 'Overall verdict' })).toBeVisible()
  await expect(table.getByText('Awaiting evidence').first()).toBeVisible()
  await expect(table.getByText('Insufficient').first()).toBeVisible()
  await expect(table.getByText('Review').first()).toBeVisible()
  await expect(table.getByRole('link', { name: 'Open run run-reviewed' })).toHaveAttribute('href', '/tests/run-reviewed')
  await expect(table.getByText('Passed', { exact: true })).toHaveCount(0)
  await expect(table.getByText('Approved', { exact: true })).toHaveCount(0)
  await expect(page.getByText('Run prepared. Evidence is still required before governance review.')).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: '/tmp/fairmind-evaluation-runs-desktop.png' })
})

test('shows truthful run detail, distinct layer axes, and exact Passport identifiers', async ({ page }) => {
  await mockEvaluationWorkbench(page, {
    plans: [basePlan],
    runs: [reviewedRun],
    detailRun: reviewedRun,
  })
  await page.goto('/tests/run-reviewed')

  await expect(page.getByRole('heading', { name: 'Evaluation run', exact: true })).toBeVisible()
  await expect(page.getByText('Technical status', { exact: true })).toBeVisible()
  await expect(page.getByText('Governance verdict', { exact: true })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Component layer verdicts' })).toContainText('Model')
  await expect(page.getByRole('region', { name: 'Component layer verdicts' })).toContainText('Tools')
  await expect(page.getByRole('region', { name: 'Risk dimension verdicts' })).toContainText('Security')
  await expect(page.getByRole('region', { name: 'Risk dimension verdicts' })).toContainText('Governance')
  await expect(page.getByText('evidence-run-418', { exact: true })).toBeVisible()
  await expect(page.getByText('passport-revision-7', { exact: true })).toBeVisible()
  await expect(page.getByText(/import \{MlopsRunLinks\}/)).toHaveCount(0)
  await expect(page.getByText('// ...', { exact: true })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Back to Evaluation Runs' })).toHaveAttribute('href', '/tests')
})

test('labels absent layer axes as not assessed and never invents evidence', async ({ page }) => {
  await mockEvaluationWorkbench(page, {
    plans: [basePlan],
    runs: [awaitingRun],
    detailRun: awaitingRun,
  })
  await page.goto('/tests/run-awaiting')

  await expect(page.getByRole('region', { name: 'Component layer verdicts' }).getByText('Not assessed')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Risk dimension verdicts' }).getByText('Not assessed')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Evidence Passport linkage' }).getByText('Awaiting evidence', { exact: true })).toBeVisible()
  await expect(page.getByText('Synthetic artifact', { exact: true })).toHaveCount(0)
})

test('separates loading, server failure, and focused action failure states', async ({ page }) => {
  await mockEvaluationWorkbench(page, { listDelayMs: 500 })
  await page.goto('/tests')
  await expect(page.getByLabel('Loading evaluation workspace')).toBeVisible()
  await expect(page.getByText('No evaluation runs yet', { exact: true })).toBeVisible()

  await page.unroute('**/api/proxy/**')
  await mockEvaluationWorkbench(page, { listError: true })
  await page.reload()
  const serverAlert = page.getByRole('alert').filter({ hasText: 'Evaluation data unavailable' })
  await expect(serverAlert).toContainText('Evaluation plan service unavailable')
  await expect(serverAlert.getByRole('button', { name: 'Retry loading evaluations' })).toBeVisible()
  await expect(page.getByRole('form', { name: 'Create evaluation plan' })).toHaveCount(0)
  await expect(page.getByText('Plan availability is unconfirmed', { exact: true })).toBeVisible()

  await page.unroute('**/api/proxy/**')
  await mockEvaluationWorkbench(page, {
    plans: [basePlan],
    createRunError: true,
  })
  await page.reload()
  await page.getByRole('button', { name: 'Prepare evidence run' }).click()
  const actionAlert = page.getByRole('alert').filter({ hasText: 'Run preparation is temporarily blocked.' })
  await expect(actionAlert).toContainText('Use an imported report or retry after the executor is connected.')
  await expect(actionAlert).toBeFocused()
})
