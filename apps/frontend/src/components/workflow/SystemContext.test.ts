import assert from 'node:assert/strict'
import test from 'node:test'

import { chooseSelectedSystemId } from './SystemContext'

const systemIds = ['system-1', 'system-2']

test('prefers a valid stored system over the initialized fallback selection', () => {
  assert.equal(chooseSelectedSystemId(systemIds, 'acme-pricing-lab', 'system-2'), 'system-2')
})

test('falls back to a valid current system and then the first real system', () => {
  assert.equal(chooseSelectedSystemId(systemIds, 'system-1', 'missing'), 'system-1')
  assert.equal(chooseSelectedSystemId(systemIds, 'missing', 'also-missing'), 'system-1')
})
