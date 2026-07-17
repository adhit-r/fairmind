import { expect, test, type Page, type Route } from '@playwright/test'

const organization = {
  id: 'org-1',
  name: 'Acme Assurance',
  slug: 'acme-assurance',
  owner_id: 'user-1',
  created_at: '2026-07-17T00:00:00Z',
  role: 'admin',
}

const system = {
  id: 'system-1',
  workspaceId: 'workspace-1',
  name: 'Claims Review Agent',
  owner: 'model-owner@acme.test',
  riskTier: 'high',
  lifecycleStage: 'govern',
  readiness: 48,
  metadata: { system_type: 'agent', system_version: '2.4.1' },
}

const secondSystem = {
  id: 'system-2',
  workspaceId: 'workspace-1',
  name: 'Underwriting Copilot',
  owner: 'underwriting-owner@acme.test',
  riskTier: 'medium',
  lifecycleStage: 'govern',
  readiness: 39,
  metadata: { system_type: 'copilot', system_version: '1.2.0' },
}

const framework = { framework_key: 'aiuc-1', name: 'AIUC-1' }
const version = {
  id: 'version-aiuc-apr-2026',
  framework_key: 'aiuc-1',
  name: 'AIUC-1',
  version_label: 'April, 2026',
  source_hash: 'sha256:catalog-april-2026',
  status: 'active',
}
const previousVersion = {
  id: 'version-aiuc-jan-2026',
  framework_key: 'aiuc-1',
  name: 'AIUC-1',
  version_label: 'January, 2026',
  source_hash: 'sha256:catalog-january-2026',
  status: 'superseded',
}

const initialControls = [
  {
    id: 'assessment-a006-1',
    external_id: 'A006.1',
    title: 'Document model limitations',
    statement: 'Maintain current limitations and intended-use evidence.',
    obligation: 'mandatory',
    application: 'core',
    applicability: 'applicable',
    status: 'not_started',
    owner: null,
    accepted_evidence_count: 0,
    latest_evaluation: 'Bias suite run 418',
    latest_evaluation_at: '2026-07-15T10:30:00Z',
    freshness: 'current',
    open_findings: 1,
    parent_requirement_id: 'A006',
    parent_requirement_title: 'Documentation and transparency',
    mapping_rationale: 'Evaluation limitations and model documentation support this control.',
    evidence_trace: [
      {
        id: 'trace-1',
        label: 'Bias suite run 418',
        kind: 'FairMind evaluation',
        source: 'bias-suite',
        state: 'candidate',
        captured_at: '2026-07-15T10:30:00Z',
      },
    ],
  },
  {
    id: 'assessment-a006-2',
    external_id: 'A006.2',
    title: 'Publish user-facing disclosures',
    statement: 'Provide notices appropriate to the deployment context.',
    obligation: 'optional',
    application: 'supplemental',
    applicability: 'pending',
    status: 'partial',
    owner: 'product-counsel@acme.test',
    accepted_evidence_count: 0,
    latest_evaluation: null,
    latest_evaluation_at: null,
    freshness: 'missing',
    open_findings: 0,
  },
  {
    id: 'assessment-a007-1',
    external_id: 'A007.1',
    title: 'Review evaluation outcomes',
    statement: 'Review evaluation outcomes before material release decisions.',
    obligation: 'mandatory',
    application: 'core',
    applicability: 'applicable',
    status: 'ready_for_review',
    owner: 'governance@acme.test',
    accepted_evidence_count: 2,
    latest_evaluation: 'Safety suite run 902',
    latest_evaluation_at: '2026-07-16T09:00:00Z',
    freshness: 'current',
    open_findings: 0,
  },
]

const secondSystemControls = [{
  id: 'assessment-a010-1',
  external_id: 'A010.1',
  title: 'Maintain human escalation',
  statement: 'Document the escalation path for consequential decisions.',
  obligation: null,
  application: null,
  applicability: 'applicable',
  status: 'not_started',
  owner: null,
  accepted_evidence_count: null,
  latest_evaluation: null,
  latest_evaluation_source: null,
  latest_evaluation_at: null,
  freshness: null,
  open_findings: null,
  parent_requirement_id: null,
  parent_requirement_title: null,
  mapping_rationale: null,
  evidence_trace: null,
}]

type MockOptions = {
  catalogDelayMs?: number
  catalogError?: boolean
  emptyCatalog?: boolean
  frameworkName?: string
  initiallyAssigned?: boolean
  permissions?: string[]
  readinessDelayMs?: number
  role?: string
  secondSystemDelayMs?: number
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

async function mockWorkbench(page: Page, options: MockOptions = {}) {
  let assigned = options.initiallyAssigned ?? false
  let secondAssigned = true
  let controls = structuredClone(initialControls)
  let otherControls = structuredClone(secondSystemControls)
  const patchedAssessmentIds: string[] = []

  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'playwright-token')
    window.localStorage.setItem('selected_org_id', 'org-1')
    window.localStorage.setItem('fairmind:selected-ai-system', 'system-1')
  })

  await page.route('**/api/proxy/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace('/api/proxy', '')

    if (path === '/api/v1/auth/me') {
      return fulfillJson(route, { id: 'user-1', username: 'reviewer', email: 'reviewer@acme.test' })
    }
    if (path === '/api/v1/organizations') {
      return fulfillJson(route, {
        organizations: [{
          ...organization,
          role: options.role ?? organization.role,
          permissions: options.permissions ?? [],
        }],
      })
    }
    if (path === '/api/v1/ai-governance/systems') {
      return fulfillJson(route, [system, secondSystem])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/frameworks') {
      if (options.catalogDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.catalogDelayMs))
      }
      if (options.catalogError) {
        return fulfillJson(route, { detail: 'Framework catalog unavailable' }, 404)
      }
      return fulfillJson(route, options.emptyCatalog ? [] : [{
        ...framework,
        name: options.frameworkName ?? framework.name,
      }])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/frameworks/aiuc-1/versions') {
      return fulfillJson(route, [version, previousVersion])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/systems/system-1/framework-assignments') {
      if (request.method() === 'POST') {
        assigned = true
        return fulfillJson(route, {
          id: 'assignment-1',
          org_id: 'org-1',
          system_id: 'system-1',
          framework_version_id: version.id,
        }, 201)
      }
      return fulfillJson(route, assigned ? [{
        id: 'assignment-1',
        org_id: 'org-1',
        system_id: 'system-1',
        framework_version_id: version.id,
      }] : [])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/systems/system-2/framework-assignments') {
      if (options.secondSystemDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.secondSystemDelayMs))
      }
      if (request.method() === 'POST') {
        secondAssigned = true
        return fulfillJson(route, {
          id: 'assignment-2',
          org_id: 'org-1',
          system_id: 'system-2',
          framework_version_id: version.id,
        }, 201)
      }
      return fulfillJson(route, secondAssigned ? [{
        id: 'assignment-2',
        org_id: 'org-1',
        system_id: 'system-2',
        framework_version_id: version.id,
      }] : [])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-1/controls') {
      return fulfillJson(route, controls)
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-1/readiness') {
      if (options.readinessDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.readinessDelayMs))
      }
      const missingEvidence = controls.filter((control) => control.accepted_evidence_count === 0).length
      return fulfillJson(route, {
        applicable: 2,
        accepted: 0,
        ready_for_review: 1,
        partial: 1,
        not_started: 1,
        not_applicable: 0,
        blocking_findings: 1,
        missing_evidence: missingEvidence,
        stale_evidence: 0,
      })
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-2/controls') {
      return fulfillJson(route, otherControls)
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-2/readiness') {
      return fulfillJson(route, {
        applicable: 1,
        accepted: 0,
        ready_for_review: 0,
        partial: 0,
        not_started: 1,
        not_applicable: 0,
        blocking_findings: 0,
        missing_evidence: 0,
        stale_evidence: 0,
      })
    }
    if (path.startsWith('/api/v1/ai-governance/organizations/org-1/control-assessments/')) {
      const id = path.split('/').at(-1)
      patchedAssessmentIds.push(id || '')
      const update = request.postDataJSON()
      controls = controls.map((control) => control.id === id ? { ...control, ...update } : control)
      otherControls = otherControls.map((control) => control.id === id ? { ...control, ...update } : control)
      const updated = controls.find((control) => control.id === id)
        || otherControls.find((control) => control.id === id)
      return fulfillJson(route, {
        ...updated,
        org_id: 'org-1',
        system_id: id === 'assessment-a010-1' ? 'system-2' : 'system-1',
        framework_assignment_id: id === 'assessment-a010-1' ? 'assignment-2' : 'assignment-1',
        control_definition_id: `definition-${id}`,
        created_at: '2026-07-17T00:00:00Z',
        updated_at: '2026-07-17T12:00:00Z',
      })
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/systems/system-1/evidence-runs') {
      return fulfillJson(route, [])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/systems/system-2/evidence-runs') {
      return fulfillJson(route, [])
    }

    return fulfillJson(route, [])
  })

  return { patchedAssessmentIds }
}

test('activates a framework and completes the control review journey by keyboard', async ({ page }) => {
  await mockWorkbench(page)
  await page.goto('/compliance-dashboard')

  const workbench = page.getByTestId('framework-controls-workbench')
  await expect(workbench.getByRole('heading', { name: 'Frameworks & Controls' })).toBeVisible()
  await expect(workbench).toContainText('Activate a framework version for this AI system')

  const januaryVersion = workbench.getByRole('radio', { name: /AIUC-1 January, 2026/i })
  const aprilVersion = workbench.getByRole('radio', { name: /AIUC-1 April, 2026/i })
  await januaryVersion.focus()
  await page.keyboard.press('Space')
  await expect(januaryVersion).toBeChecked()
  await page.keyboard.press('ArrowUp')
  await expect(aprilVersion).toBeChecked()

  const activate = workbench.getByRole('button', { name: /Activate AIUC-1 April, 2026/i })
  await activate.focus()
  await page.keyboard.press('Enter')

  await expect(workbench.getByText('AIUC-1 readiness')).toBeVisible()
  await expect(workbench.getByText('A006.1', { exact: true })).toBeVisible()

  await workbench.getByRole('checkbox', { name: 'Mandatory controls' }).check()
  await workbench.getByRole('checkbox', { name: 'Missing accepted evidence' }).check()
  await expect(workbench.getByText('A006.1', { exact: true })).toBeVisible()
  await expect(workbench.getByText('A006.2', { exact: true })).toHaveCount(0)
  await expect(workbench.getByText('A007.1', { exact: true })).toHaveCount(0)

  const expand = workbench.getByRole('button', { name: /Expand control A006\.1/i })
  await expand.focus()
  await page.keyboard.press('Enter')
  const trace = workbench.getByRole('region', { name: 'Trace for A006.1' })
  await expect(trace).toBeVisible()
  await expect(trace).toContainText('Bias suite run 418')
  await expect(trace).toContainText('candidate')

  await trace.getByLabel('Control owner').fill('assurance-lead@acme.test')
  await trace.getByLabel('Applicability').selectOption('not_applicable')
  await trace.getByLabel('Assessment state').selectOption('ready_for_review')
  await trace.getByRole('button', { name: 'Save control changes' }).focus()
  await page.keyboard.press('Enter')

  await expect(trace.getByText('Changes saved')).toBeVisible()
  await expect(trace.getByLabel('Control owner')).toHaveValue('assurance-lead@acme.test')
  await expect(trace.getByLabel('Applicability')).toHaveValue('not_applicable')
  await expect(trace.getByLabel('Assessment state')).toHaveValue('ready_for_review')
  await expect(workbench).not.toContainText(/certif|compliant|compliance/i)
})

test('shows loading, empty, and recoverable catalog states', async ({ page }) => {
  await mockWorkbench(page, { catalogDelayMs: 500, emptyCatalog: true })
  await page.goto('/compliance-dashboard')
  const workbench = page.getByTestId('framework-controls-workbench')

  await expect(workbench.getByLabel('Loading framework catalog')).toBeVisible()
  await expect(workbench.getByRole('heading', { name: 'No framework versions available' })).toBeVisible()

  await page.unroute('**/api/proxy/**')
  await mockWorkbench(page, { catalogError: true })
  await page.reload()
  await expect(workbench.getByRole('alert')).toContainText('Framework catalog unavailable')
  await expect(workbench.getByRole('button', { name: 'Retry loading frameworks' })).toBeVisible()
  await expect(workbench.getByRole('heading', { name: 'No framework versions available' })).toHaveCount(0)
})

test('clears the previous assignment before loading another system scope', async ({ page }) => {
  const mocks = await mockWorkbench(page, { initiallyAssigned: true, secondSystemDelayMs: 650 })
  await page.goto('/compliance-dashboard')
  const workbench = page.getByTestId('framework-controls-workbench')

  await expect(workbench.getByText('A006.1', { exact: true })).toBeVisible()
  await page.getByRole('combobox', { name: 'System scope' }).click()
  await page.getByRole('option', { name: secondSystem.name }).click()

  await expect(workbench.getByText('A006.1', { exact: true })).toHaveCount(0)
  await expect(workbench.getByLabel('Loading framework catalog')).toBeVisible()
  await expect(workbench.getByText('A010.1', { exact: true })).toBeVisible()
  expect(mocks.patchedAssessmentIds).not.toContain('assessment-a006-1')
})

test('uses framework names dynamically and enforces read-only governance access', async ({ page }) => {
  await mockWorkbench(page, {
    frameworkName: 'Review Standard',
    initiallyAssigned: true,
    role: 'viewer',
    permissions: ['model:read'],
  })
  await page.goto('/compliance-dashboard')
  const workbench = page.getByTestId('framework-controls-workbench')

  await expect(workbench.getByRole('heading', { name: 'Review Standard readiness' })).toBeVisible()
  await workbench.getByRole('button', { name: /Expand control A006\.1/i }).click()
  const trace = workbench.getByRole('region', { name: 'Trace for A006.1' })
  await expect(trace.getByText('Read-only access')).toBeVisible()
  await expect(trace.getByLabel('Control owner')).toHaveCount(0)

  await workbench.getByRole('radio', { name: /AIUC-1 January, 2026/i }).check()
  await expect(workbench.getByRole('button', { name: /Activate AIUC-1 January, 2026/i })).toBeDisabled()
})

test('does not present unresolved readiness counts as zero', async ({ page }) => {
  await mockWorkbench(page, { initiallyAssigned: true, readinessDelayMs: 650 })
  await page.goto('/compliance-dashboard')
  const readiness = page.getByRole('region', { name: 'AIUC-1 readiness' })

  await expect(readiness.getByLabel('Loading readiness summary')).toBeVisible()
  await expect(readiness.locator('dd', { hasText: /^0$/ })).toHaveCount(0)
  await expect(readiness.getByLabel('Loading readiness summary')).toHaveCount(0)
  await expect(readiness.locator('dd').first()).toHaveText('2')
})

test('permits model writers to activate and edit controls', async ({ page }) => {
  await mockWorkbench(page, { role: 'member', permissions: ['model:write'] })
  await page.goto('/compliance-dashboard')
  const workbench = page.getByTestId('framework-controls-workbench')

  await workbench.getByRole('button', { name: /Activate AIUC-1 April, 2026/i }).click()
  await workbench.getByRole('button', { name: /Expand control A006\.1/i }).click()
  await expect(workbench.getByLabel('Control owner')).toBeEditable()
})

test('keeps the expanded trace inline in the mobile stacked record', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await mockWorkbench(page)
  await page.goto('/compliance-dashboard')

  const workbench = page.getByTestId('framework-controls-workbench')
  await workbench.getByRole('radio', { name: /AIUC-1 April, 2026/i }).check()
  await workbench.getByRole('button', { name: /Activate AIUC-1 April, 2026/i }).click()
  await workbench.getByRole('button', { name: /Expand control A006\.1/i }).click()

  const record = workbench.getByTestId('control-record-A006.1')
  await expect(record.getByText('Owner', { exact: true })).toBeVisible()
  await expect(record.getByText('Accepted evidence', { exact: true })).toBeVisible()
  await expect(record.getByRole('region', { name: 'Trace for A006.1' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})
