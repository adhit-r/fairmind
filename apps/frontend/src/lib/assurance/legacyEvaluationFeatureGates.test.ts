import assert from 'node:assert/strict'
import test from 'node:test'

import {
  allowedLegacyDeliveryModes,
  allowedLegacyEnforcementModes,
  resolveLegacyEvaluationFeatureGates,
} from './legacyEvaluationFeatureGates'

test('legacy evaluation feature gates default-deny automatic enforcement, workers, and legacy evidence linking', () => {
  const gates = resolveLegacyEvaluationFeatureGates({})

  assert.deepEqual(gates, {
    legacyEvidenceLinking: false,
  })
  assert.deepEqual(allowedLegacyEnforcementModes(), ['advisory', 'human_approval'])
  assert.deepEqual(allowedLegacyDeliveryModes(), ['external_provider', 'imported_report'])
})

test('retired automatic and worker environment flags cannot revive unsupported capabilities', () => {
  const retiredEnvironment = {
    automaticEnforcement: 'true',
    fairmindWorkerDelivery: 'true',
    legacyEvidenceLinking: '1',
  }
  const gates = resolveLegacyEvaluationFeatureGates(retiredEnvironment)

  assert.deepEqual(gates, {
    legacyEvidenceLinking: false,
  })
  assert.deepEqual(allowedLegacyEnforcementModes(), ['advisory', 'human_approval'])
  assert.deepEqual(allowedLegacyDeliveryModes(), ['external_provider', 'imported_report'])
})
