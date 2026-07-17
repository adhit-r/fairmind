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
const nistFramework = { framework_key: 'nist-ai-rmf', name: 'NIST AI RMF' }
const nistVersion = {
  id: 'version-nist-1',
  framework_key: 'nist-ai-rmf',
  name: 'NIST AI RMF',
  version_label: '1.0',
  source_hash: 'sha256:nist-ai-rmf-1',
  status: 'active',
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

const additionalAssignmentControls = [{
  id: 'assessment-a020-1',
  external_id: 'A020.1',
  title: 'Review agent tool boundaries',
  statement: 'Evaluate and document tool-use boundaries for deployed agents.',
  obligation: 'mandatory',
  application: 'agent',
  applicability: 'applicable',
  status: 'not_started',
  owner: null,
  accepted_evidence_count: 0,
  latest_evaluation: null,
  latest_evaluation_at: null,
  freshness: 'missing',
  open_findings: 0,
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
  evidenceRuns?: Array<Record<string, unknown>>
  artifactEvidence?: Array<Record<string, unknown>>
  secondArtifactEvidence?: Array<Record<string, unknown>>
  secondEvidenceDelayMs?: number
  multipleAssignments?: boolean
  mappingConflictOnce?: boolean
  multipleFrameworks?: boolean
  environmentalImpact?: Record<string, unknown>
  savedReports?: Array<Record<string, unknown>>
}

function evidenceRun(controlAssessmentId = 'assessment-a006-1', mappingId = 'mapping-418-a006-1') {
  return {
    id: 'evidence-run-418',
    run_id: 'bias-418',
    evidence_id: 'artifact-run-418',
    content_hash: '0f33e89a6d6e6eefecf4afc92c837bd259f036e599acc653f401b87eab30bf55',
    result: 'passed_with_limitations',
    source_type: 'fairmind_evaluation',
    source_identifier: 'FairMind Bias Suite',
    captured_at: '2026-07-15T10:30:00Z',
    suite_name: 'Bias and subgroup parity',
    suite_version: '2026.07',
    subject_version: '2.4.1',
    runner_version: 'fairmind-runner 1.8.0',
    assurance_source: 'fairmind_internal',
    limitations: ['Sparse intersectional cohorts were excluded below n=30.'],
    candidate_mappings: [{
      id: mappingId,
      evidence_id: 'artifact-run-418',
      control_assessment_id: controlAssessmentId,
      state: 'candidate',
      rationale: 'Evaluation limitations and version metadata support documentation review.',
      review_version: 0,
      review_history: [] as Array<Record<string, unknown>>,
    }],
  }
}

function evidenceArtifact(id: string, systemId: string, title: string) {
  return {
    id,
    systemId,
    type: 'policy',
    title,
    source: 'manual',
    status: 'draft',
    uploadedBy: 'reviewer@acme.test',
    capturedAt: '2026-07-14T08:00:00Z',
    content: {},
    confidence: 0.9,
    metadata: {},
    tags: ['limitations'],
    folder: 'AIUC-1',
    artifactKind: 'narrative',
    fileUrl: '',
    fileName: '',
    fileSize: 0,
    timestamp: '2026-07-14T08:00:00Z',
    stale: false,
    linkedEntityCount: 0,
    linkedEntities: [],
    metadataSummary: {},
    workflowState: 'collected',
  }
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
  let evidenceRuns = structuredClone(options.evidenceRuns ?? [])
  const artifactEvidence = structuredClone(options.artifactEvidence ?? [])
  const secondArtifactEvidence = structuredClone(options.secondArtifactEvidence ?? [])
  let mappingConflictPending = options.mappingConflictOnce ?? false
  let approvalRequest: Record<string, unknown> | null = null
  let approvalDecisions: Array<Record<string, unknown>> = []
  let savedReports = structuredClone(options.savedReports ?? [])

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
      }, ...(options.multipleFrameworks ? [nistFramework] : [])])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/frameworks/aiuc-1/versions') {
      return fulfillJson(route, [version, previousVersion])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/frameworks/nist-ai-rmf/versions') {
      return fulfillJson(route, [nistVersion])
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
      return fulfillJson(route, assigned ? [...(options.multipleFrameworks ? [{
        id: 'assignment-nist',
        org_id: 'org-1',
        system_id: 'system-1',
        framework_version_id: nistVersion.id,
      }] : []), {
        id: 'assignment-1',
        org_id: 'org-1',
        system_id: 'system-1',
        framework_version_id: version.id,
      }, ...(options.multipleAssignments ? [{
        id: 'assignment-3',
        org_id: 'org-1',
        system_id: 'system-1',
        framework_version_id: previousVersion.id,
      }] : [])] : [])
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
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-nist/controls') {
      return fulfillJson(route, [{
        ...additionalAssignmentControls[0],
        id: 'assessment-nist-map-1',
        external_id: 'GOVERN-1.1',
        title: 'Establish AI governance accountability',
      }])
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-3/controls') {
      return fulfillJson(route, additionalAssignmentControls)
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
    if (path === '/api/v1/ai-governance/organizations/org-1/framework-assignments/assignment-nist/readiness') {
      return fulfillJson(route, {
        applicable: 1,
        accepted: 1,
        ready_for_review: 0,
        partial: 0,
        not_started: 0,
        not_applicable: 0,
        blocking_findings: 0,
        missing_evidence: 0,
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
      return fulfillJson(route, evidenceRuns)
    }
    if (path === '/api/v1/ai-governance/organizations/org-1/systems/system-2/evidence-runs') {
      return fulfillJson(route, [])
    }
    if (path.startsWith('/api/v1/ai-governance/organizations/org-1/evidence-mappings/') && path.endsWith('/review')) {
      if (mappingConflictPending) {
        mappingConflictPending = false
        return fulfillJson(route, { detail: 'Mapping review changed by another reviewer' }, 409)
      }
      const mappingId = path.split('/').at(-2)
      const review = request.postDataJSON()
      let reviewed: Record<string, unknown> | undefined
      evidenceRuns = evidenceRuns.map((run) => ({
        ...run,
        candidate_mappings: (run.candidate_mappings as Array<Record<string, unknown>> | undefined)?.map((mapping) => {
          if (mapping.id !== mappingId) return mapping
          reviewed = {
            ...mapping,
            state: review.state,
            rationale: review.rationale,
            review_version: Number(mapping.review_version) + 1,
            review_history: [{
              state: review.state,
              rationale: review.rationale,
              reviewed_by: 'user-1',
              reviewed_at: '2026-07-17T12:15:00Z',
            }],
          }
          return reviewed
        }),
      }))
      return fulfillJson(route, reviewed)
    }
    if (path === '/api/v1/ai-governance/evidence-v2/system-1') {
      return fulfillJson(route, artifactEvidence)
    }
    if (path === '/api/v1/ai-governance/evidence-v2/system-2') {
      if (options.secondEvidenceDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.secondEvidenceDelayMs))
      }
      return fulfillJson(route, secondArtifactEvidence)
    }
    if (path === '/api/v1/ai-governance/evidence/system-1/summary') {
      return fulfillJson(route, {
        systemId: 'system-1',
        totalEvidence: artifactEvidence.length,
        linkedEvidence: 0,
        averageConfidence: 0.9,
        highConfidenceEvidence: artifactEvidence.length,
        evidenceTypes: [],
        metadataSources: [],
        workflowState: artifactEvidence.length ? 'collected' : 'empty',
        decisionReadiness: 'needs_evidence',
        missingSignals: ['Independent reviewer sign-off'],
        recommendedNextStep: 'Review evaluation mappings before assurance reporting.',
      })
    }
    if (path === '/api/v1/ai-governance/evidence/system-2/summary') {
      if (options.secondEvidenceDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.secondEvidenceDelayMs))
      }
      return fulfillJson(route, {
        systemId: 'system-2',
        totalEvidence: secondArtifactEvidence.length,
        linkedEvidence: 0,
        averageConfidence: 0.8,
        highConfidenceEvidence: secondArtifactEvidence.length,
        evidenceTypes: [],
        metadataSources: [],
        workflowState: secondArtifactEvidence.length ? 'collected' : 'empty',
        decisionReadiness: 'needs_evidence',
        missingSignals: [],
        recommendedNextStep: '',
      })
    }
    if (path === '/api/v1/ai-governance/evidence-item/artifact-1/links' && request.method() === 'POST') {
      const link = request.postDataJSON()
      return fulfillJson(route, {
        id: 'link-1',
        entityType: link.entity_type,
        entityId: link.entity_id,
        createdAt: '2026-07-17T12:30:00Z',
      }, 201)
    }
    if (path === '/api/v1/ai-governance/compliance/frameworks') {
      return fulfillJson(route, [])
    }
    if (path === '/api/v1/ai-governance/approval/system/system-1') {
      return fulfillJson(route, { systemId: system.id, request: approvalRequest, decisions: approvalDecisions })
    }
    if (path === '/api/v1/ai-governance/approval/system/system-1/request' && request.method() === 'POST') {
      approvalRequest = {
        id: 'approval-1',
        status: 'pending',
        requested_by: 'model-owner@acme.test',
        createdAt: '2026-07-17T13:00:00Z',
      }
      return fulfillJson(route, { systemId: system.id, request: approvalRequest, decisions: approvalDecisions })
    }
    if (path === '/api/v1/ai-governance/approval-requests/approval-1/decision' && request.method() === 'POST') {
      const decision = request.postDataJSON()
      approvalDecisions = [...approvalDecisions, {
        decision: decision.decision,
        notes: decision.notes,
        decidedBy: decision.decided_by,
        decidedAt: '2026-07-17T13:15:00Z',
      }]
      approvalRequest = approvalRequest ? { ...approvalRequest, status: decision.decision } : null
      return fulfillJson(route, approvalDecisions.at(-1))
    }
    if (path === '/api/v1/systems/system-1/environmental-impact') {
      return fulfillJson(route, options.environmentalImpact ?? {})
    }
    if (path === '/api/v1/ai-governance/reports' && request.method() === 'GET') {
      return fulfillJson(route, savedReports)
    }
    if (path === '/api/v1/ai-governance/reports/generate' && request.method() === 'POST') {
      const generated = {
        id: `report-${savedReports.length + 1}`,
        systemId: system.id,
        reportType: 'governance',
        title: 'Governance Assurance Summary',
        generatedBy: 'reviewer@acme.test',
        config: request.postDataJSON(),
        data: {
          system: { name: system.name, owner: system.owner, riskTier: system.riskTier, lifecycleStage: system.lifecycleStage, readiness: system.readiness },
          risks: [], evidence: [], remediation: [], approvals: [], generatedAt: '2026-07-17T14:00:00Z',
        },
        createdAt: '2026-07-17T14:00:00Z',
      }
      savedReports = [generated, ...savedReports]
      return fulfillJson(route, generated, 201)
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

test('reviews a provenance-rich evaluation mapping and links artifacts through a real control picker', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    evidenceRuns: [{
      id: 'evidence-run-418',
      run_id: 'bias-418',
      evidence_id: 'artifact-run-418',
      content_hash: '0f33e89a6d6e6eefecf4afc92c837bd259f036e599acc653f401b87eab30bf55',
      result: 'passed_with_limitations',
      source_type: 'fairmind_evaluation',
      source_identifier: 'FairMind Bias Suite',
      captured_at: '2026-07-15T10:30:00Z',
      suite_name: 'Bias and subgroup parity',
      suite_version: '2026.07',
      subject_version: '2.4.1',
      runner_version: 'fairmind-runner 1.8.0',
      assurance_source: 'fairmind_internal',
      limitations: ['Sparse intersectional cohorts were excluded below n=30.'],
      candidate_mappings: [{
        id: 'mapping-418-a006-1',
        evidence_id: 'artifact-run-418',
        control_assessment_id: 'assessment-a006-1',
        state: 'candidate',
        rationale: 'Evaluation limitations and version metadata support documentation review.',
        review_version: 0,
        review_history: [],
      }],
    }],
    artifactEvidence: [{
      id: 'artifact-1',
      systemId: 'system-1',
      type: 'policy',
      title: 'Model limitation register',
      source: 'manual',
      status: 'draft',
      uploadedBy: 'reviewer@acme.test',
      capturedAt: '2026-07-14T08:00:00Z',
      content: {},
      confidence: 0.9,
      metadata: {},
      tags: ['limitations'],
      folder: 'AIUC-1',
      artifactKind: 'narrative',
      fileUrl: '',
      fileName: '',
      fileSize: 0,
      timestamp: '2026-07-14T08:00:00Z',
      stale: false,
      linkedEntityCount: 0,
      linkedEntities: [],
      metadataSummary: {},
      workflowState: 'collected',
    }],
  })

  await page.goto('/evidence?view=evaluations')
  const surface = page.getByTestId('evidence-evaluations-surface')
  await expect(surface.getByRole('heading', { name: 'Evidence & Evaluations' })).toBeVisible()
  await expect(page).toHaveURL(/view=evaluations/)

  const run = surface.getByRole('article', { name: 'Evaluation run Bias and subgroup parity' })
  await expect(run).toContainText('FairMind Bias Suite')
  await expect(run).toContainText('System version 2.4.1')
  await expect(run).toContainText('Runner version fairmind-runner 1.8.0')
  await expect(run).toContainText('Captured Jul 15, 2026')
  await expect(run).toContainText('passed with limitations')
  await expect(run).toContainText('Sparse intersectional cohorts were excluded below n=30.')
  await expect(run).toContainText('0f33e89a6d6e6eefecf4afc92c837bd259f036e599acc653f401b87eab30bf55')

  const mapping = run.getByRole('region', { name: 'Mapping review for A006.1' })
  await expect(mapping).toContainText('Evaluation limitations and version metadata support documentation review.')
  await mapping.getByLabel('Review rationale for A006.1').fill('Accepted after checking the versioned limitation register.')
  await mapping.getByRole('button', { name: 'Accept mapping to A006.1' }).click()
  await expect(mapping).toContainText('Accepted')
  await expect(mapping).toContainText('Accepted after checking the versioned limitation register.')

  await surface.getByRole('link', { name: 'Artifacts' }).click()
  await expect(page).toHaveURL(/view=artifacts/)
  await surface.getByRole('button', { name: /Model limitation register/i }).click()
  await page.getByRole('button', { name: 'Link entity' }).click()
  await expect(page.getByLabel('Entity ID')).toHaveCount(0)
  await page.getByLabel('Search framework controls').fill('A006.1')
  await page.getByRole('button', { name: /Select A006.1 Document model limitations/i }).click()
  await page.getByRole('button', { name: 'Add link' }).click()
  await expect(page.getByText('A006.1 — Document model limitations')).toBeVisible()
})

test('aggregates controls from every framework assignment for evaluation mappings', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    multipleAssignments: true,
    evidenceRuns: [evidenceRun('assessment-a020-1', 'mapping-418-a020-1')],
    artifactEvidence: [evidenceArtifact('artifact-1', 'system-1', 'Agent tool boundary register')],
  })

  await page.goto('/evidence?view=evaluations')
  const mapping = page.getByRole('region', { name: 'Mapping review for A020.1' })
  await expect(mapping).toContainText('Review agent tool boundaries')

  await page.getByRole('link', { name: 'Artifacts' }).click()
  await page.getByRole('button', { name: /Agent tool boundary register/i }).click()
  await page.getByRole('button', { name: 'Link entity' }).click()
  await page.getByLabel('Search framework controls').fill('A020.1')
  await expect(page.getByRole('button', { name: /Select A020.1 Review agent tool boundaries/i })).toBeVisible()
})

test('clears evidence artifacts and stale drawer state when system scope changes', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    artifactEvidence: [evidenceArtifact('artifact-1', 'system-1', 'Claims limitation register')],
    secondArtifactEvidence: [evidenceArtifact('artifact-2', 'system-2', 'Underwriting escalation log')],
    secondEvidenceDelayMs: 500,
  })

  await page.goto('/evidence?view=artifacts')
  await page.getByRole('button', { name: /Claims limitation register/i }).click()
  await expect(page.getByRole('heading', { name: 'Claims limitation register' })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('heading', { name: 'Claims limitation register' })).toHaveCount(0)

  await page.getByRole('combobox', { name: 'System scope' }).click()
  await page.getByRole('option', { name: secondSystem.name }).click()

  await expect(page.getByRole('button', { name: /Claims limitation register/i })).toHaveCount(0)
  await expect(page.getByText(`Loading evidence for ${secondSystem.name}`)).toBeVisible()
  await expect(page.getByRole('button', { name: /Underwriting escalation log/i })).toBeVisible()
})

test('keeps evaluation mapping review controls read-only for viewers', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    role: 'viewer',
    permissions: ['model:read'],
    evidenceRuns: [evidenceRun()],
  })

  await page.goto('/evidence?view=evaluations')
  const mapping = page.getByRole('region', { name: 'Mapping review for A006.1' })
  await expect(page.getByText('Read-only evidence access')).toBeVisible()
  await expect(mapping).toContainText('Read-only access')
  await expect(mapping.getByRole('button', { name: /Accept mapping/i })).toHaveCount(0)
  await expect(mapping.getByLabel(/Review rationale/i)).toHaveCount(0)
})

test('offers a mapping reload action after an optimistic review conflict', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    mappingConflictOnce: true,
    evidenceRuns: [evidenceRun()],
  })

  await page.goto('/evidence?view=evaluations')
  const mapping = page.getByRole('region', { name: 'Mapping review for A006.1' })
  await mapping.getByRole('button', { name: 'Accept mapping to A006.1' }).click()
  await expect(mapping.getByRole('alert')).toContainText('another reviewer')
  await mapping.getByRole('button', { name: 'Reload mapping' }).click()
  await expect(mapping.getByRole('alert')).toHaveCount(0)
})

test('shows framework scope and backend blockers before the overview readiness aggregate', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    evidenceRuns: [evidenceRun()],
  })

  await page.goto('/ai-governance')
  const overview = page.getByTestId('governance-assurance-overview')

  await expect(overview.getByRole('heading', { name: 'AI Governance Assurance' })).toBeVisible()
  const scope = overview.getByRole('region', { name: 'Assurance scope' })
  await expect(scope).toContainText('Acme Assurance')
  await expect(scope).toContainText('Claims Review Agent')
  await expect(scope).toContainText('AIUC-1')
  await expect(scope).toContainText('April, 2026')

  const blockers = overview.getByRole('region', { name: 'Readiness blockers' })
  await expect(blockers).toContainText('1 rejected assessment')
  await expect(blockers).toContainText('2 controls missing accepted evidence')
  await expect(blockers).toContainText('No stale evidence reported')

  const readiness = overview.getByRole('region', { name: 'AIUC-1 readiness' })
  await expect(readiness).toContainText('2 applicable')
  await expect(readiness).toContainText('0 accepted')
  await expect(readiness).toContainText('1 partial')
  await expect(readiness).toContainText('1 not started')

  const text = await overview.innerText()
  expect(text.indexOf('READINESS BLOCKERS')).toBeLessThan(text.indexOf('AIUC-1 READINESS'))
  await expect(overview).not.toContainText(/compliance rate|evidence completeness|go$|certif/i)
})

test('presents a version-pinned assurance summary with evidence hashes and review decisions', async ({ page }) => {
  const acceptedRun = evidenceRun()
  acceptedRun.candidate_mappings[0] = {
    ...acceptedRun.candidate_mappings[0],
    state: 'accepted',
    review_version: 1,
    review_history: [{
      state: 'accepted',
      rationale: 'Accepted after checking the versioned limitation register.',
      reviewed_by: 'user-1',
      reviewed_at: '2026-07-17T12:15:00Z',
    }],
  }
  await mockWorkbench(page, { initiallyAssigned: true, evidenceRuns: [acceptedRun] })

  await page.goto('/reports?view=builder')
  const report = page.getByTestId('assurance-report')

  await expect(report.getByRole('heading', { name: 'Reports & Assurance' })).toBeVisible()
  await expect(report.getByText('Builder mode', { exact: true })).toBeVisible()
  await expect(report.getByRole('region', { name: 'Assurance scope' })).toContainText('AIUC-1 April, 2026')
  await expect(report.getByRole('region', { name: 'Evidence index' })).toContainText(
    '0f33e89a6d6e6eefecf4afc92c837bd259f036e599acc653f401b87eab30bf55',
  )
  await expect(report.getByRole('region', { name: 'Evidence index' })).toContainText('FairMind Bias Suite')
  await expect(report.getByRole('region', { name: 'Unresolved findings' })).toContainText('1 rejected assessment')
  await expect(report.getByRole('region', { name: 'Decision register' })).toContainText('Accepted')
  await expect(report.getByRole('region', { name: 'Decision register' })).toContainText(
    'Accepted after checking the versioned limitation register.',
  )
  await expect(report.getByRole('region', { name: 'Limitations' })).toContainText(
    'Sparse intersectional cohorts were excluded below n=30.',
  )
  await expect(report.getByRole('link', { name: 'Review control assessments' })).toBeVisible()
  await expect(report).not.toContainText(/certified|compliant/i)
})

test('uses the reports route as a read-only auditor lens and redirects legacy bookmarks', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    evidenceRuns: [evidenceRun()],
    role: 'viewer',
    permissions: ['model:read'],
  })

  await page.goto('/reports')
  const report = page.getByTestId('assurance-report')
  await expect(report.getByText('Auditor mode', { exact: true })).toBeVisible()
  await expect(report).toContainText('Read-only auditor view')
  await expect(report.getByRole('link', { name: 'Review control assessments' })).toHaveCount(0)
  await expect(report.getByRole('link', { name: 'Review evidence mappings' })).toHaveCount(0)

  await page.goto('/audit-reports')
  await expect(page).toHaveURL(/\/reports\?view=builder$/)
  await page.goto('/compliance')
  await expect(page).toHaveURL(/\/compliance-dashboard$/)
  await page.goto('/compliance/dashboard')
  await expect(page).toHaveURL(/\/compliance-dashboard$/)
  await page.goto('/remediation-wizard')
  await expect(page).toHaveURL(/\/remediation\?mode=guided$/)
})

test('retains persisted approval decisions and environmental governance on the assurance overview', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    environmentalImpact: {
      systemId: system.id,
      generatedAt: '2026-07-16T08:00:00Z',
      version: 'env-3',
      totals: { energyKwh: 92.4, carbonKgCo2e: 31.8, computeHours: 14.2 },
      recommendation: { status: 'conditional', summary: 'Reduce inference intensity before the next review.' },
      provenance: { source: 'Cloud Carbon Footprint', methodology: 'location-based', boundary: 'training and inference' },
      evidenceLinks: [{ id: 'env-evidence-1', title: 'Cloud energy export', source: 'company_integration' }],
    },
  })

  await page.goto('/ai-governance')
  const overview = page.getByTestId('governance-assurance-overview')
  const approval = overview.getByRole('region', { name: 'Approval decision' })
  await approval.getByRole('button', { name: 'Submit for approval' }).click()
  await expect(approval).toContainText('Pending')
  await expect(approval.getByRole('button', { name: 'Approve request' })).toBeVisible()
  await expect(approval.getByRole('button', { name: 'Reject request' })).toBeVisible()
  await approval.getByRole('button', { name: 'Approve request' }).click()
  await expect(approval).toContainText('Approved')

  const environmental = overview.getByRole('region', { name: 'Environmental governance' })
  await expect(environmental.getByRole('heading', { name: 'Environmental Governance' })).toBeVisible()
  await expect(environmental).toContainText('92.4 kWh')
  await expect(environmental).toContainText('31.8 kg CO2e')
  await expect(environmental).toContainText('Conditional')
  await expect(environmental).toContainText('Cloud energy export')
})

test('matches each selected assignment to its own framework version across multiple catalogs', async ({ page }) => {
  await mockWorkbench(page, { initiallyAssigned: true, multipleFrameworks: true })

  await page.goto('/ai-governance')
  const overview = page.getByTestId('governance-assurance-overview')
  await expect(overview.getByRole('region', { name: 'Assurance scope' })).toContainText('NIST AI RMF 1.0')
  await overview.getByRole('combobox', { name: 'Framework scope' }).selectOption('assignment-1')
  await expect(overview.getByRole('region', { name: 'Assurance scope' })).toContainText('AIUC-1 April, 2026')

  await page.goto('/reports?view=builder')
  const report = page.getByTestId('assurance-report')
  await expect(report.getByRole('region', { name: 'Assurance scope' })).toContainText('NIST AI RMF 1.0')
  await report.getByRole('combobox', { name: 'Framework scope' }).selectOption('assignment-1')
  await expect(report.getByRole('region', { name: 'Assurance scope' })).toContainText('AIUC-1 April, 2026')
})

test('keeps report generation, preview, saved history, and exports reachable on reports', async ({ page }) => {
  await mockWorkbench(page, {
    initiallyAssigned: true,
    savedReports: [{
      id: 'saved-report-1',
      systemId: system.id,
      reportType: 'governance',
      title: 'July assurance snapshot',
      generatedBy: 'reviewer@acme.test',
      config: { frameworks: ['AIUC-1 April, 2026'], sections: [] },
      data: { system: { name: system.name, owner: system.owner, riskTier: system.riskTier, lifecycleStage: system.lifecycleStage, readiness: 48 }, generatedAt: '2026-07-16T12:00:00Z' },
      createdAt: '2026-07-16T12:00:00Z',
    }],
  })

  await page.goto('/reports?view=builder')
  const studio = page.getByRole('region', { name: 'Report builder and history' })
  await expect(studio.getByRole('heading', { name: 'Assurance Report Studio' })).toBeVisible()
  await expect(studio).toContainText('July assurance snapshot')
  await expect(studio.getByRole('button', { name: 'JSON' })).toBeVisible()
  await expect(studio.getByRole('button', { name: 'PDF' })).toBeVisible()
  const downloadPromise = page.waitForEvent('download')
  await studio.getByRole('button', { name: 'JSON' }).click()
  expect((await downloadPromise).suggestedFilename()).toBe('July_assurance_snapshot.json')
  await studio.getByRole('button', { name: 'Generate report' }).click()
  await expect(studio.getByRole('heading', { name: 'Claims Review Agent' })).toBeVisible()
  await expect(studio).toContainText('Governance Assurance Summary')
})
