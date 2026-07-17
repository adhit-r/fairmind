import assert from 'node:assert/strict'
import test from 'node:test'

import { API_ENDPOINTS } from '../endpoints'
import { NAVIGATION_ITEMS } from '../../constants/navigation'

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
