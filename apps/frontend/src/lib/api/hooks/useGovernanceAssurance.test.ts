import assert from 'node:assert/strict'
import test from 'node:test'

import { API_ENDPOINTS } from '../endpoints'
import { NAVIGATION_ITEMS } from '../../constants/navigation'
import type {
  ControlAssessmentUpdateResult,
  EvidenceMappingReviewInput,
  EvidenceRunInput,
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

test('keeps evidence artifact references and mapping review versions in request contracts', () => {
  const evidenceRun: EvidenceRunInput = {
    sourceType: 'evaluation',
    sourceIdentifier: 'bias-suite',
    runId: 'run-1',
    artifactReferences: [{ uri: 's3://customer/evaluations/run-1.json', sha256: 'a'.repeat(64) }],
  }
  const review: EvidenceMappingReviewInput = {
    state: 'accepted',
    rationale: 'Coverage verified.',
    reviewVersion: 2,
  }

  assert.equal(evidenceRun.artifactReferences?.[0]?.sha256.length, 64)
  assert.deepEqual(review, { state: 'accepted', rationale: 'Coverage verified.', reviewVersion: 2 })
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
