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
    fairmindWorkerDelivery: false,
    legacyEvidenceLinking: false,
  })
  assert.deepEqual(allowedLegacyEnforcementModes(), ['advisory', 'human_approval'])
  assert.deepEqual(allowedLegacyDeliveryModes(gates), ['external_provider', 'imported_report'])
})

test('legacy automatic enforcement stays unavailable when the old environment flag is true', () => {
  const retiredEnvironment = {
    automaticEnforcement: 'true',
    fairmindWorkerDelivery: 'TRUE',
    legacyEvidenceLinking: '1',
  }
  const gates = resolveLegacyEvaluationFeatureGates(retiredEnvironment)

  assert.deepEqual(gates, {
    fairmindWorkerDelivery: false,
    legacyEvidenceLinking: false,
  })
  assert.deepEqual(allowedLegacyEnforcementModes(), ['advisory', 'human_approval'])
  assert.deepEqual(allowedLegacyDeliveryModes(gates), ['external_provider', 'imported_report'])
})
