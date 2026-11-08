import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'
import { runHook, stub } from './runHookForTest'
import { NAVIGATION_ITEMS } from '../../constants/navigation'
import { EvaluationRunList } from '../../../app/(dashboard)/evidence/components/EvaluationRunList'
import type {
  ControlAssessmentUpdateResult,
  EvidenceMappingReviewInput,
  EvidencePassportInput,
  EvidenceRun,
  FrameworkImportResult,
} from './useGovernanceAssurance'

async function governanceContract() {
  try {
    return await import('./useGovernanceAssurance')
  } catch (error) {
    assert.fail(`Expected governance assurance contract to load: ${String(error)}`)
  }
}

test('builds organization and system scoped framework assignment URLs', () => {
  assert.equal(
    API_ENDPOINTS.aiGovernance.frameworkAssignments?.('org-1', 'system-9'),
    '/api/v1/ai-governance/organizations/org-1/systems/system-9/framework-assignments',
  )
})

test('normalizes snake case assurance payloads into the frontend contract', async () => {
  const { normalizeGovernanceResponse } = await governanceContract()

  assert.deepEqual(
    normalizeGovernanceResponse({
      framework_key: 'aiuc-1',
      version_label: 'April, 2026',
      source_hash: 'catalog-hash',
      candidate_mappings: [{
        control_assessment_id: 'assessment-1',
        review_version: 2,
        review_history: [{ reviewed_by: 'reviewer-1', reviewed_at: '2026-07-17T00:00:00Z' }],
      }],
    }),
    {
      frameworkKey: 'aiuc-1',
      versionLabel: 'April, 2026',
      sourceHash: 'catalog-hash',
      candidateMappings: [{
        controlAssessmentId: 'assessment-1',
        reviewVersion: 2,
        reviewHistory: [{ reviewedBy: 'reviewer-1', reviewedAt: '2026-07-17T00:00:00Z' }],
      }],
    },
  )
})

test('keeps camel case payloads and exposes empty and API error states', async () => {
  const { normalizeGovernanceList, unwrapGovernanceResponse } = await governanceContract()

  assert.deepEqual(normalizeGovernanceList([]), [])
  assert.deepEqual(
    unwrapGovernanceResponse({ success: true, data: { reviewVersion: 3 } }),
    { reviewVersion: 3 },
  )
  assert.throws(
    () => unwrapGovernanceResponse({ success: false, error: 'Organization membership required' }),
    /Organization membership required/,
  )
})

test('normalizes framework imports and raw assessment update results', async () => {
  const { normalizeGovernanceResponse } = await governanceContract()
  const imported: FrameworkImportResult = {
    versionId: 'version-1',
    frameworkKey: 'aiuc-1',
    versionLabel: 'April, 2026',
    requirementCount: 51,
    controlCount: 135,
    sourceHash: 'catalog-hash',
    created: true,
  }
  const updated: ControlAssessmentUpdateResult = {
    id: 'assessment-1',
    orgId: 'org-1',
    systemId: 'system-1',
    frameworkAssignmentId: 'assignment-1',
    controlDefinitionId: 'control-1',
    applicability: 'applicable',
    status: 'partial',
    owner: null,
    createdAt: '2026-07-17T00:00:00Z',
    updatedAt: '2026-07-17T01:00:00Z',
  }

  assert.deepEqual(
    normalizeGovernanceResponse({
      version_id: 'version-1', framework_key: 'aiuc-1', version_label: 'April, 2026',
      requirement_count: 51, control_count: 135, source_hash: 'catalog-hash', created: true,
    }),
    imported,
  )
  assert.deepEqual(
    normalizeGovernanceResponse({
      id: 'assessment-1', org_id: 'org-1', system_id: 'system-1',
      framework_assignment_id: 'assignment-1', control_definition_id: 'control-1',
      applicability: 'applicable', status: 'partial', owner: null,
      created_at: '2026-07-17T00:00:00Z', updated_at: '2026-07-17T01:00:00Z',
    }),
    updated,
  )
})

test('posts the complete Evidence Passport without a compact-envelope conversion', async () => {
  const { evidencePassportRequestBody } = await governanceContract()
  const passport: EvidencePassportInput = {
    schemaVersion: '1.0.0',
    passportId: 'passport-1',
    passportRevision: 1,
    claimBoundary: 'supporting_evidence_only',
    organizationId: 'org-1',
    workspaceId: 'workspace-1',
    aiSystem: {
      systemId: 'system-1', name: 'System one', kind: 'model', version: '1', identityHash: '1'.repeat(64),
    },
    evaluation: {
      sourceType: 'fairmind_evaluation', sourceIdentifier: 'bias-suite', runId: 'run-1',
      capabilityState: 'validated', assuranceSource: 'fairmind_internal',
      evaluator: { name: 'Evaluator', version: '1', adapterName: 'adapter', adapterVersion: '1', runnerVersion: '1' },
      suite: { name: 'Bias suite', version: '1' },
      subject: { kind: 'model', subjectId: 'subject-1', name: 'Subject', version: '1', digest: '2'.repeat(64) },
      scope: { intendedUse: 'Bounded test', inputFingerprint: '3'.repeat(64), sampleCount: 10, exclusions: [] },
      configurationHash: '4'.repeat(64), thresholds: [],
      result: { status: 'passed', summary: 'Passed bounded test', metrics: [], startedAt: '2026-07-18T00:00:00Z', endedAt: '2026-07-18T00:01:00Z' },
      runContentHash: '5'.repeat(64), capturedAt: '2026-07-18T00:01:00Z', limitations: [],
    },
    artifacts: [{
      artifactId: 'artifact-1', role: 'report', uri: 's3://customer/evaluations/run-1.json',
      sha256: '6'.repeat(64), mediaType: 'application/json', containsSensitiveData: false,
    }],
    frameworkMappings: [],
    review: { status: 'pending', reviewVersion: 0 },
    findings: [], remediation: [],
    freshness: { status: 'current', policy: 'Retest on change', assessedAt: '2026-07-18T00:01:00Z', staleReasons: [], invalidationKeys: [] },
    lineage: { predecessorPassportIds: [], retestOfPassportIds: [] },
    createdAt: '2026-07-18T00:01:00Z', canonicalContentHash: '7'.repeat(64),
  }
  const body = evidencePassportRequestBody(passport)
  const review: EvidenceMappingReviewInput = {
    state: 'accepted',
    rationale: 'Coverage verified.',
    reviewVersion: 2,
  }

  assert.equal(body.artifacts[0]?.sha256.length, 64)
  assert.equal(body.evaluation.runContentHash.length, 64)
  assert.equal(body.canonicalContentHash.length, 64)
  assert.equal('artifactReferences' in body, false)
  assert.equal('controlExternalIds' in body, false)
  assert.deepEqual(review, { state: 'accepted', rationale: 'Coverage verified.', reviewVersion: 2 })

  const publicRevision: EvidencePassportInput['passportRevision'] = 1
  const publicReview: EvidencePassportInput['review']['status'] = 'pending'
  const publicMappingState: EvidencePassportInput['frameworkMappings'][number]['state'] = 'candidate'
  assert.equal(publicRevision, 1)
  assert.equal(publicReview, 'pending')
  assert.equal(publicMappingState, 'candidate')

  // @ts-expect-error Public evaluator ingestion cannot submit later revisions.
  const laterRevision: EvidencePassportInput['passportRevision'] = 2
  // @ts-expect-error Public evaluator ingestion cannot submit reviewed passports.
  const reviewedPassport: EvidencePassportInput['review']['status'] = 'accepted'
  // @ts-expect-error Public evaluator ingestion accepts candidate mappings only.
  const acceptedMapping: EvidencePassportInput['frameworkMappings'][number]['state'] = 'accepted'
  // @ts-expect-error Public evaluator ingestion has no predecessor field.
  const predecessorKey: keyof EvidencePassportInput = 'previousRevisionHash'
  // @ts-expect-error Public evaluator ingestion has no signature field.
  const signaturesKey: keyof EvidencePassportInput = 'signatures'
  void laterRevision
  void reviewedPassport
  void acceptedMapping
  void predecessorKey
  void signaturesKey

  type RemediationInput = EvidencePassportInput['remediation'][number]
  // @ts-expect-error ownerId is required by the canonical Evidence Passport schema.
  const ownerlessRemediation: RemediationInput = {
    remediationId: 'remediation-1',
    findingIds: ['finding-1'],
    status: 'planned',
    action: 'Resolve the bounded finding.',
  }
  void ownerlessRemediation
})

test('the evaluation-list consumer renders the backward-compatible GET DTO', async () => {
  const { evidenceRunDisplayName } = await governanceContract()
  const run: EvidenceRun = {
    id: 'stored-run-1', runId: 'run-1', evidenceId: null,
    contentHash: 'a'.repeat(64), runContentHash: 'a'.repeat(64),
    passportId: 'passport-1', latestRevision: 2, latestCanonicalContentHash: 'b'.repeat(64),
    capabilityState: 'validated', result: 'passed', sourceType: 'fairmind_evaluation',
    sourceIdentifier: 'bias-suite', capturedAt: '2026-07-18T00:01:00Z',
    suiteName: 'Bias suite', suiteVersion: '1', subjectVersion: '1', runnerVersion: '1',
    assuranceSource: 'fairmind_internal', limitations: [], artifacts: [], candidateMappings: [],
  }

  assert.equal(evidenceRunDisplayName(run), 'Bias suite')
  assert.equal(run.contentHash, run.runContentHash)
  assert.equal(run.latestRevision, 2)
  assert.equal(run.passportId, 'passport-1')
  const markup = renderToStaticMarkup(createElement(EvaluationRunList, {
    runs: [run], controls: [], loading: false, error: null, canReview: false,
    onReview: async () => { throw new Error('No mapping is rendered in this fixture') },
    onRefresh: async () => {},
  }))
  assert.match(markup, /Evaluation run Bias suite/)
  assert.match(markup, /bias-suite/)
  assert.match(markup, /Content hash/)
})

test('keeps Govern & Prove to the six assurance destinations', () => {
  const governance = NAVIGATION_ITEMS.find((category) => category.id === 'compliance')

  assert.deepEqual(
    governance?.items?.map(({ title, href }) => [title, href]),
    [
      ['Overview', '/ai-governance'],
      ['AI Systems', '/model-inventory'],
      ['Frameworks & Controls', '/compliance-dashboard'],
      ['Evidence & Evaluations', '/evidence'],
      ['Findings', '/risks'],
      ['Reports & Assurance', '/reports'],
    ],
  )
})

test('resolves every system assignment to its matching framework version', async () => {
  const { resolveFrameworkAssignments } = await governanceContract()
  const resolved = resolveFrameworkAssignments(
    [
      { frameworkKey: 'aiuc-1', name: 'AIUC-1' },
      { frameworkKey: 'nist-ai-rmf', name: 'NIST AI RMF' },
    ],
    [
      { id: 'version-aiuc', frameworkKey: 'aiuc-1', name: 'AIUC-1', versionLabel: 'April, 2026', sourceHash: 'aiuc-hash', status: 'active' },
      { id: 'version-nist', frameworkKey: 'nist-ai-rmf', name: 'NIST AI RMF', versionLabel: '1.0', sourceHash: 'nist-hash', status: 'active' },
    ],
    [
      { id: 'assignment-nist', orgId: 'org-1', systemId: 'system-1', frameworkVersionId: 'version-nist' },
      { id: 'assignment-aiuc', orgId: 'org-1', systemId: 'system-1', frameworkVersionId: 'version-aiuc' },
    ],
  )

  assert.deepEqual(
    resolved.map(({ assignment, framework, version }) => [assignment.id, framework.frameworkKey, version.id]),
    [
      ['assignment-nist', 'nist-ai-rmf', 'version-nist'],
      ['assignment-aiuc', 'aiuc-1', 'version-aiuc'],
    ],
  )
})

test('framework assignments from another system surface as an error, never as data', async () => {
  const { useFrameworkAssignments, GovernanceScopeMismatchError } = await governanceContract()
  const get = stub(apiClient, 'get', async () => ({
    success: true,
    data: [
      { id: 'assignment-1', orgId: 'org-1', systemId: 'system-1', frameworkVersionId: 'version-1' },
      { id: 'assignment-2', orgId: 'org-1', systemId: 'system-2', frameworkVersionId: 'version-1' },
    ],
  }))
  try {
    const { result, states } = runHook(() => useFrameworkAssignments('org-1', 'system-1'))
    await result.refresh()
    assert.ok(states[0].error instanceof GovernanceScopeMismatchError)
    assert.deepEqual(states[0].data, [])
  } finally {
    get()
  }
})

test('matching framework assignments load normally', async () => {
  const { useFrameworkAssignments } = await governanceContract()
  const assignment = { id: 'assignment-1', orgId: 'org-1', systemId: 'system-1', frameworkVersionId: 'version-1' }
  const get = stub(apiClient, 'get', async () => ({ success: true, data: [assignment] }))
  try {
    const { result, states } = runHook(() => useFrameworkAssignments('org-1', 'system-1'))
    await result.refresh()
    assert.equal(states[0].error, null)
    assert.deepEqual(states[0].data, [assignment])
  } finally {
    get()
  }
})

test('a framework assignment created for another organization is rejected', async () => {
  const { useFrameworkAssignments } = await governanceContract()
  const post = stub(apiClient, 'post', async () => ({
    success: true,
    data: { id: 'assignment-1', orgId: 'org-2', systemId: 'system-1', frameworkVersionId: 'version-1' },
  }))
  try {
    const { result } = runHook(() => useFrameworkAssignments('org-1', 'system-1'))
    await assert.rejects(result.assign('version-1'), /requested orgId/)
  } finally {
    post()
  }
})

test('a control assessment update answered for another organization or record is rejected', async () => {
  const { useFrameworkAssignmentControls } = await governanceContract()
  const updated: ControlAssessmentUpdateResult = {
    id: 'assessment-1', orgId: 'org-2', systemId: 'system-1', frameworkAssignmentId: 'assignment-1',
    controlDefinitionId: 'control-1', applicability: 'applicable', status: 'accepted', owner: null,
    createdAt: '2026-07-17T00:00:00Z', updatedAt: '2026-07-17T00:00:00Z',
  }
  const patch = stub(apiClient, 'patch', async () => ({ success: true, data: updated }))
  try {
    const { result } = runHook(() => useFrameworkAssignmentControls('org-1', 'assignment-1'))
    await assert.rejects(result.updateAssessment('assessment-1', { status: 'accepted' }), /requested orgId/)
    await assert.rejects(result.updateAssessment('assessment-9', { status: 'accepted' }), /requested id/)
  } finally {
    patch()
  }
})

test('an evidence run ingested for a different passport is rejected', async () => {
  const { useEvidenceRuns } = await governanceContract()
  const post = stub(apiClient, 'post', async () => ({
    success: true,
    data: { id: 'evidence-run-1', runId: 'run-1', passportId: 'passport-other' },
  }))
  try {
    const { result } = runHook(() => useEvidenceRuns('org-1', 'system-1'))
    const passport = { passportId: 'passport-1', evaluation: { runId: 'run-1' } } as EvidencePassportInput
    await assert.rejects(result.ingestRun(passport), /requested passportId/)
  } finally {
    post()
  }
})

test('evidence mappings for another control or mapping record set the error state', async () => {
  const { useEvidenceMappingReview, GovernanceScopeMismatchError } = await governanceContract()
  const post = stub(apiClient, 'post', async () => ({
    success: true,
    data: { id: 'mapping-other', evidenceId: 'evidence-1', controlAssessmentId: 'assessment-other' },
  }))
  try {
    const { result, states } = runHook(() => useEvidenceMappingReview('org-1'))
    await assert.rejects(result.createMapping('evidence-1', 'assessment-1'), /requested controlAssessmentId/)
    assert.ok(states[1] instanceof GovernanceScopeMismatchError)
    states[1] = null
    const review: EvidenceMappingReviewInput = { state: 'accepted', reviewVersion: 1 }
    await assert.rejects(result.reviewMapping('mapping-1', review), /requested id/)
    assert.ok(states[1] instanceof GovernanceScopeMismatchError)
  } finally {
    post()
  }
})
