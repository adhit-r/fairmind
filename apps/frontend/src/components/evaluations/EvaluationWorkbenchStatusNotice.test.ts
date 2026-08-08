import assert from 'node:assert/strict'
import test from 'node:test'

import { EvaluationWorkbenchRequestError } from '@/lib/api/hooks/useEvaluationWorkbenchV2'

import { evaluationWorkbenchFailureState } from './EvaluationWorkbenchStatusNotice'

test('identifies a 403 evaluation response as denied rather than unavailable', () => {
  const error = new EvaluationWorkbenchRequestError('Evaluation records are forbidden.', {
    message: 'Evaluation records are forbidden.',
    status: 403,
    type: 'client',
    canRetry: false,
  })

  assert.deepEqual(evaluationWorkbenchFailureState(error), {
    kind: 'denied',
    title: 'Evaluation access denied',
    message: 'You do not have permission to view this scoped evaluation data. No records were displayed.',
  })
})

test('keeps non-permission errors in the unavailable state', () => {
  assert.deepEqual(evaluationWorkbenchFailureState(new Error('Network unavailable.')), {
    kind: 'unavailable',
    title: 'Evaluation data unavailable',
    message: 'Network unavailable.',
  })
})
