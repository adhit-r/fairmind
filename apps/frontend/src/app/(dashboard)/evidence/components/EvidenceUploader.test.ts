import assert from 'node:assert/strict'
import { test } from 'node:test'

import { otherTypeHint } from './EvidenceUploader'

test('an Other evidence type is described by what the release gate does with it', () => {
  assert.deepEqual(otherTypeHint(' Policy '), { text: "Counts toward the release gate's Human oversight check as manual evidence.", blocked: false })
  assert.deepEqual(otherTypeHint('provenance'), { text: "Counts toward the release gate's Data governance check as manual evidence.", blocked: false })
  for (const measured of ['fairness_test', 'Monitoring', 'drift', 'environmental_assessment', 'Evaluation_Run']) assert.equal(otherTypeHint(measured).blocked, true, measured)
  assert.deepEqual(otherTypeHint('vendor_contract'), { text: 'The release gate does not count this type.', blocked: false })
})
