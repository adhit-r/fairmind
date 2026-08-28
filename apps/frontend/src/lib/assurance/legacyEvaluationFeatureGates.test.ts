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
    automaticEnforcement: false,
    fairmindWorkerDelivery: false,
    legacyEvidenceLinking: false,
  })
  assert.deepEqual(allowedLegacyEnforcementModes(gates), ['advisory', 'human_approval'])
  assert.deepEqual(allowedLegacyDeliveryModes(gates), ['external_provider', 'imported_report'])
})

test('legacy evaluation feature gates require literal true for each independently enabled capability', () => {
  const gates = resolveLegacyEvaluationFeatureGates({
    automaticEnforcement: 'true',
    fairmindWorkerDelivery: 'TRUE',
    legacyEvidenceLinking: '1',
  })

  assert.deepEqual(gates, {
    automaticEnforcement: true,
    fairmindWorkerDelivery: false,
    legacyEvidenceLinking: false,
  })
  assert.deepEqual(allowedLegacyEnforcementModes(gates), [
    'advisory',
    'human_approval',
    'automatic',
  ])
  assert.deepEqual(allowedLegacyDeliveryModes(gates), ['external_provider', 'imported_report'])
})
