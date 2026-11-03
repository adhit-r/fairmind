import { expect, test, type BrowserContext, type Page, type Route } from '@playwright/test'
import path from 'node:path'

const APP_URL = process.env.FAIRMIND_DOCS_BASE_URL || 'http://localhost:1112'
const OUTPUT_DIR = path.resolve(process.cwd(), '../docs/public/media/product/v1')

const MODEL_ID = 'model-docs-claims-triage'
const SYSTEM_ID = 'system-docs-claims-triage'
const ASSESSMENT_ID = 'assessment-docs-environmental-v1'

const MODEL = {
  id: MODEL_ID,
  name: 'Claims Triage Model',
  version: '1.4.0',
  type: 'classification',
  status: 'active',
  createdAt: '2026-07-15T09:00:00Z',
  updatedAt: '2026-07-31T10:00:00Z',
  description: 'Prioritises inbound insurance claims for manual review.',
  fairness_score: 0,
  bias_score: 0,
  tags: ['claims', 'triage', 'human-review'],
}

const SYSTEM = {
  id: SYSTEM_ID,
  workspaceId: 'workspace-fairmind-docs',
  name: 'Claims Triage Model',
  owner: 'model-risk@fairmind.local',
  riskTier: 'high',
  lifecycleStage: 'govern',
  readiness: 62,
  metadata: { scenario: 'docs-fixture' },
}

const CONTROLS = [
  { code: 'ENV-1', name: 'Assessment boundary', governance_test: 'Boundary declared.', optional: false },
  { code: 'ENV-2', name: 'Energy accounting', governance_test: 'Total kWh measured.', optional: false },
  { code: 'ENV-3', name: 'Dual carbon accounting', governance_test: 'Location and market carbon.', optional: false },
  { code: 'ENV-4', name: 'Efficiency metric', governance_test: 'Per functional unit.', optional: false },
  { code: 'ENV-5', name: 'Evidence confidence', governance_test: 'Provenance and uncertainty.', optional: false },
  { code: 'ENV-6', name: 'Mitigation and approval', governance_test: 'Mitigation or exception.', optional: false },
]

const ENVIRONMENTAL_PACKET = {
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
          message: 'Conditional go requires documented mitigation or a valid exception.',
        },
      ],
      result: {
        recommendation: 'conditional_go',
        impact_tier: 'high',
        confidence_score: 0.93,
        confidence_band: 'measured',
        provenance_class: 'measured',
        mitigation_blocking: true,
        approval_blocking: true,
        coverage_rate: 0.8333,
      },
    },
    versionTrail: [],
  },
}

const EVIDENCE = [
  {
    id: 'evidence-docs-measurement',
    systemId: SYSTEM_ID,
    type: 'environmental_measurement',
    title: 'Inference energy measurement packet',
    source: 'measurement_harness',
    status: 'collected',
    uploadedBy: 'docs-reviewer@fairmind.local',
    capturedAt: '2026-07-31T10:00:00Z',
    content: { scope: 'in-region inference serving' },
    confidence: 0.93,
    metadata: { provenance: 'measured' },
    tags: ['environment', 'inference'],
    folder: 'Environmental review',
    artifactKind: 'attestation',
    fileUrl: '',
    fileName: '',
    fileSize: 0,
    timestamp: '2026-07-31T10:00:00Z',
    stale: false,
    linkedEntityCount: 1,
    linkedEntities: [{ id: 'link-docs-1', entityType: 'assessment', entityId: ASSESSMENT_ID, createdAt: '2026-07-31T10:05:00Z' }],
    metadataSummary: { provenance: 'measured' },
    workflowState: 'linked',
  },
  {
    id: 'evidence-docs-boundary',
    systemId: SYSTEM_ID,
    type: 'assessment_boundary',
    title: 'Serving boundary and functional unit',
    source: 'reviewer_attestation',
    status: 'collected',
    uploadedBy: 'docs-reviewer@fairmind.local',
    capturedAt: '2026-07-31T09:30:00Z',
    content: { functional_unit: '1000_requests' },
    confidence: 0.88,
    metadata: { provenance: 'reviewed' },
    tags: ['boundary', 'reviewed'],
    folder: 'Environmental review',
    artifactKind: 'narrative',
    fileUrl: '',
    fileName: '',
    fileSize: 0,
    timestamp: '2026-07-31T09:30:00Z',
    stale: false,
    linkedEntityCount: 1,
    linkedEntities: [{ id: 'link-docs-2', entityType: 'system', entityId: SYSTEM_ID, createdAt: '2026-07-31T09:35:00Z' }],
    metadataSummary: { provenance: 'reviewed' },
    workflowState: 'linked',
  },
  {
    id: 'evidence-docs-retest',
    systemId: SYSTEM_ID,
    type: 'retest_plan',
    title: 'Mitigation re-test plan',
    source: 'model_risk_team',
    status: 'draft',
    uploadedBy: 'docs-reviewer@fairmind.local',
    capturedAt: '2026-07-31T09:00:00Z',
    content: { state: 'planned' },
    confidence: 0.72,
    metadata: { provenance: 'manual' },
    tags: ['retest', 'mitigation'],
    folder: 'Remediation',
    artifactKind: 'narrative',
    fileUrl: '',
    fileName: '',
    fileSize: 0,
    timestamp: '2026-07-31T09:00:00Z',
    stale: false,
    linkedEntityCount: 0,
    linkedEntities: [],
    metadataSummary: { provenance: 'manual' },
    workflowState: 'collected',
  },
]

const EVIDENCE_SUMMARY = {
  systemId: SYSTEM_ID,
  totalEvidence: 3,
  linkedEvidence: 2,
  averageConfidence: 0.84,
  highConfidenceEvidence: 2,
  evidenceTypes: [
    { type: 'environmental_measurement', count: 1 },
    { type: 'assessment_boundary', count: 1 },
    { type: 'retest_plan', count: 1 },
  ],
  metadataSources: [{ source: 'docs_fixture', count: 3 }],
  workflowState: 'in_review',
  decisionReadiness: 'needs_evidence',
  missingSignals: ['documented mitigation', 'passing re-test evidence'],
  recommendedNextStep: 'Document mitigation, run the re-test, and link the result.',
}

const RISK_RESPONSE = {
  risks: [
    {
      id: 'risk-docs-env-1',
      systemId: SYSTEM_ID,
      title: 'Environmental mitigation is not documented',
      severity: 'high',
      status: 'open',
      description: 'The conditional decision has no dated mitigation.',
      mitigation: 'Record an owned mitigation and re-run the gate.',
      timestamp: '2026-07-31T10:00:00Z',
    },
  ],
  summary: {
    total: 1,
    open: 1,
    automated: 0,
    bySeverity: { low: 0, medium: 0, high: 1, critical: 0 },
  },
}

const REMEDIATION_TASKS = [
  {
    id: 'remediation-docs-env-1',
    systemId: SYSTEM_ID,
    title: 'Document mitigation and re-run the environmental gate',
    description: 'Assign an owner, record the target date, then attach the passing re-test result.',
    sourceType: 'governance_blocker',
    sourceId: 'risk-docs-env-1',
    linkedRiskIds: ['risk-docs-env-1'],
    owner: 'Model Risk Team',
    priority: 'high',
    dueDate: '2026-08-14',
    status: 'in_progress',
    retestRequired: true,
    retestStatus: 'pending',
    notes: 'Dated mitigation plan\nPassing environmental gate result\nReviewer sign-off note',
    createdAt: '2026-07-31T10:15:00Z',
    updatedAt: '2026-07-31T10:30:00Z',
  },
  {
    id: 'remediation-docs-boundary-1',
    systemId: SYSTEM_ID,
    title: 'Confirm the inference measurement boundary',
    description: 'Review the recorded functional unit and serving-region scope.',
    sourceType: 'evidence_gap',
    sourceId: '',
    linkedRiskIds: [],
    owner: 'Assurance Reviewer',
    priority: 'medium',
    dueDate: null,
    status: 'done',
    retestRequired: false,
    retestStatus: 'not_started',
    notes: 'Reviewed boundary note',
    createdAt: '2026-07-30T14:00:00Z',
    updatedAt: '2026-07-31T09:30:00Z',
  },
]

const APPROVAL_STATE = {
  systemId: SYSTEM_ID,
  request: {
    id: 'approval-docs-pending',
    workflow_id: 'workflow-docs-release',
    entity_type: 'ai_system',
    entity_id: SYSTEM_ID,
    requested_by: 'model-risk@fairmind.local',
    status: 'pending',
    current_step: 1,
    decision_notes: 'Awaiting mitigation and re-test evidence.',
    createdAt: '2026-07-31T10:45:00Z',
    updatedAt: '2026-07-31T10:45:00Z',
  },
  decisions: [],
}

const FRAMEWORKS = [
  {
    id: 'framework-eu-ai-act',
    name: 'EU AI Act',
    description: 'Risk management and human oversight controls for the documented scenario.',
    compliance_score: 78,
    controls: [{ id: 'euai-risk', name: 'Risk management' }, { id: 'euai-human', name: 'Human oversight' }],
  },
  {
    id: 'framework-nist-ai-rmf',
    name: 'NIST AI RMF',
    description: 'Govern, map, measure, and manage controls for the documented scenario.',
    compliance_score: 74,
    controls: [{ id: 'nist-govern', name: 'Govern' }, { id: 'nist-measure', name: 'Measure' }],
  },
]

const POLICIES = [
  {
    id: 'policy-docs-release-gate',
    name: 'Claims Triage Release Gate',
    framework: 'NIST AI RMF',
    description: 'Requires linked evidence and closed high-priority remediation before approval.',
    rules: [],
    status: 'active',
    createdAt: '2026-07-15T09:00:00Z',
  },
]

async function installDocsFixture(context: BrowserContext) {
  await context.addInitScript(({ systemId }) => {
    if (!window.location.protocol.startsWith('http')) return
    window.localStorage.setItem('access_token', 'fairmind-docs-capture')
    window.localStorage.setItem('selected_org_id', 'org-fairmind-docs')
    window.localStorage.setItem('fairmind:selected-ai-system', systemId)
  }, { systemId: SYSTEM_ID })

  await context.route('**/api/v1/**', async (route: Route) => {
    const request = route.request()
    const url = new URL(request.url())
    const pathname = url.pathname.replace(/^\/api\/proxy/, '')
    const method = request.method()
    let status = 200
    let body: unknown = {}

    if (pathname === '/api/v1/auth/me') {
      body = {
        id: 'user-fairmind-docs',
        username: 'docs-reviewer',
        email: 'docs-reviewer@fairmind.local',
        full_name: 'Docs Reviewer',
        role: 'admin',
        is_active: true,
      }
    } else if (pathname === '/api/v1/organizations') {
      body = {
        organizations: [
          {
            id: 'org-fairmind-docs',
            name: 'FairMind Docs Lab',
            slug: 'fairmind-docs-lab',
            owner_id: 'user-fairmind-docs',
            created_at: '2026-07-15T09:00:00Z',
            role: 'admin',
          },
        ],
      }
    } else if (pathname === '/api/v1/ai-governance/systems') {
      body = [SYSTEM]
    } else if (pathname === `/api/v1/core/models/${MODEL_ID}`) {
      body = { model: MODEL }
    } else if (pathname === '/api/v1/core/models') {
      body = { data: [MODEL], count: 1 }
    } else if (pathname === '/api/v1/core/datasets') {
      body = { datasets: [], total: 0, page: 1, limit: 100 }
    } else if (pathname === `/api/v1/ai-governance/models/${MODEL_ID}/system`) {
      body = { governed: true, modelId: MODEL_ID, system: { id: SYSTEM_ID, name: SYSTEM.name } }
    } else if (pathname === `/api/v1/systems/${SYSTEM_ID}/environmental-impact`) {
      body = ENVIRONMENTAL_PACKET
    } else if (pathname === '/api/v1/environment/controls') {
      body = { controls: CONTROLS, coverage: null }
    } else if (pathname === '/api/v1/ai-governance/environment/assess' && method === 'POST') {
      body = {
        success: true,
        evidence_id: 'evidence-docs-measurement',
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
    } else if (pathname === `/api/v1/ai-governance/evidence-v2/${SYSTEM_ID}`) {
      body = EVIDENCE
    } else if (pathname === `/api/v1/ai-governance/evidence/${SYSTEM_ID}/summary`) {
      body = EVIDENCE_SUMMARY
    } else if (pathname === '/api/v1/ai-governance/dashboard/risk') {
      body = RISK_RESPONSE
    } else if (pathname === '/api/v1/ai-governance/remediation') {
      body = { tasks: REMEDIATION_TASKS, summary: { systemId: SYSTEM_ID } }
    } else if (pathname === `/api/v1/ai-governance/approval/system/${SYSTEM_ID}`) {
      body = APPROVAL_STATE
    } else if (pathname === '/api/v1/ai-governance/compliance/frameworks') {
      body = FRAMEWORKS
    } else if (pathname === '/api/v1/ai-governance/policies') {
      body = POLICIES
    } else if (pathname === '/api/v1/ai-governance/workspaces') {
      body = [{ id: 'workspace-fairmind-docs', name: 'FairMind Docs Lab' }]
    } else if (pathname.startsWith(`/api/v1/systems/${SYSTEM_ID}/environmental-impact/`) && pathname.endsWith('/approve')) {
      status = 409
      body = { detail: 'Conditional go requires documented mitigation before sign-off.' }
    }

    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    })
  })
}

async function settlePage(page: Page, heading: ReturnType<Page['getByRole']>) {
  await expect(heading).toBeVisible({ timeout: 20_000 })
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' })
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        caret-color: transparent !important;
      }
    `,
  })
  await page.evaluate(async () => {
    await document.fonts.ready
  })
}

async function capture(page: Page, filename: string) {
  expect(page.url()).not.toContain('/login')
  await page.screenshot({
    path: path.join(OUTPUT_DIR, filename),
    animations: 'disabled',
    caret: 'hide',
    fullPage: false,
  })
}

test.describe.configure({ mode: 'serial' })

test.beforeEach(async ({ context }) => {
  await installDocsFixture(context)
})

test('captures model registration with synthetic fields', async ({ page }) => {
  await page.goto(`${APP_URL}/models`, { waitUntil: 'domcontentloaded' })
  await settlePage(page, page.getByRole('heading', { name: 'Model Registry' }))
  await page.getByRole('button', { name: 'Register Model' }).first().click()
  await expect(page.getByRole('heading', { name: 'Register New Model' })).toBeVisible()
  await page.getByLabel('Model ID *').fill(MODEL_ID)
  await page.getByLabel('Name *').fill(MODEL.name)
  await page.getByLabel('Model Type *').fill(MODEL.type)
  await page.getByLabel('Version *').fill(MODEL.version)
  await page.getByLabel('Description *').fill(MODEL.description)
  await page.getByLabel('Capabilities (comma-separated) *').fill('classification, human-review routing')
  await page.getByLabel('Input Format *').fill('JSON claim record')
  await page.getByLabel('Output Format *').fill('priority score and review reason')
  await capture(page, 'model-registry-registration.png')
})

test('captures the environmental conditional gate', async ({ page }) => {
  await page.goto(`${APP_URL}/models/${MODEL_ID}`, { waitUntil: 'domcontentloaded' })
  const heading = page.getByRole('heading', { name: 'Environmental Impact' })
  await settlePage(page, heading)
  await expect(page.getByText('CONDITIONAL GO').first()).toBeVisible()
  await expect(page.getByText('0.93')).toBeVisible()
  await heading.scrollIntoViewIfNeeded()
  await page.evaluate(() => window.scrollBy(0, -80))
  await capture(page, 'environmental-gate-decision.png')
})

test('captures the evidence capability register', async ({ page }) => {
  await page.goto(`${APP_URL}/evidence`, { waitUntil: 'domcontentloaded' })
  await settlePage(page, page.getByRole('heading', { name: 'Evidence Workbench' }))
  await expect(page.getByText('Evidence Generator Workbench', { exact: true })).toBeVisible()
  await expect(page.getByText('metadata_only').first()).toBeVisible()
  await capture(page, 'evidence-capability-register.png')
})

test('captures the release gate with blockers', async ({ page }) => {
  await page.goto(`${APP_URL}/ai-governance`, { waitUntil: 'domcontentloaded' })
  await settlePage(page, page.getByRole('heading', { name: /Can Claims Triage Model Move Forward/i }))
  await expect(page.getByText('No-Go').first()).toBeVisible()
  await expect(page.getByText(/high-severity risk/i).first()).toBeVisible()
  await capture(page, 'release-gate-blockers.png')
})

test('captures the remediation re-test queue', async ({ page }) => {
  await page.goto(`${APP_URL}/remediation`, { waitUntil: 'domcontentloaded' })
  await settlePage(page, page.getByRole('heading', { name: /Remediation Turns Risks Into Owned Work/i }))
  const queueHeading = page.getByRole('heading', { name: 'Remediation queue' })
  await expect(queueHeading).toBeVisible()
  await expect(page.getByText('Document mitigation and re-run the environmental gate')).toBeVisible()
  await queueHeading.scrollIntoViewIfNeeded()
  await page.evaluate(() => window.scrollBy(0, -80))
  await capture(page, 'remediation-retest-queue.png')
})

test('captures the pending release report', async ({ page }) => {
  await page.goto(`${APP_URL}/reports`, { waitUntil: 'domcontentloaded' })
  await settlePage(page, page.getByRole('heading', { name: /Reports should prove what got approved and why/i }))
  await expect(page.getByText('Pending approval').first()).toBeVisible()
  await expect(page.getByText('67%').first()).toBeVisible()
  await capture(page, 'release-readiness-report.png')
})
