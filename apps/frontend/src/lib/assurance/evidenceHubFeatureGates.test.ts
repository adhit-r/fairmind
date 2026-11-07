import assert from 'node:assert/strict'
import test from 'node:test'

import { resolveEvidenceHubFeatureGates } from './evidenceHubFeatureGates'

test('untrusted external evidence linking defaults off and requires literal true', () => {
  assert.deepEqual(resolveEvidenceHubFeatureGates({}), {
    untrustedExternalEvidenceLinking: false,
  })
  assert.deepEqual(
    resolveEvidenceHubFeatureGates({ untrustedExternalEvidenceLinking: 'TRUE' }),
    { untrustedExternalEvidenceLinking: false },
  )
  assert.deepEqual(
    resolveEvidenceHubFeatureGates({ untrustedExternalEvidenceLinking: 'true' }),
    { untrustedExternalEvidenceLinking: true },
  )
})
