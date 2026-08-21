import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildEvidenceTrustPresentation,
  type EvidenceTrustSuiteInput,
} from './evidenceTrust'

const currentFreshness = {
  recordedFreshnessStatus: 'current',
  freshnessContractVersion: '1.0.0' as const,
  freshnessEvaluatedAt: '2026-08-09T00:00:00+00:00',
  freshnessEffectiveAt: '2026-08-08T00:00:00+00:00',
  expiringAt: '2026-08-30T00:00:00+00:00',
  freshnessReasonCodes: [] as string[],
  decisionEvidenceEligible: true,
}

function suiteExecution(
  overrides: Partial<EvidenceTrustSuiteInput> = {},
): EvidenceTrustSuiteInput {
  return {
    id: 'suite-execution-1',
    suiteVersionId: 'suite-version-1',
    ownerScope: 'organization',
    ordinal: 1,
    technicalStatus: 'succeeded',
    evidenceResultStatus: 'passed',
    admissionStatus: 'verified',
    reviewStatus: 'accepted',
    freshnessStatus: 'current',
    ...currentFreshness,
    limitations: [],
    failureCode: null,
    failureMessage: null,
    ...overrides,
  }
}

test('keeps execution, evaluator evidence, and governance verdict as independently labeled axes', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'leased',
    evidenceOutcome: 'passed_with_limitations',
    overallVerdict: 'review',
  })

  assert.deepEqual(presentation.axes, [
    { label: 'Execution status', value: 'Leased' },
    { label: 'Evaluator evidence result', value: 'Passed with limitations' },
    { label: 'Governance verdict', value: 'Review' },
  ])
})

test('marks signer and reviewer identity unavailable when the run response does not provide them', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'approved',
    suiteExecutions: [{
      id: 'suite-execution-1',
      suiteVersionId: 'suite-version-1',
      ownerScope: 'organization',
      ordinal: 1,
      technicalStatus: 'succeeded',
      evidenceResultStatus: 'passed',
      admissionStatus: 'verified',
      reviewStatus: 'accepted',
      freshnessStatus: 'current',
      ...currentFreshness,
      limitations: [],
      failureCode: null,
      failureMessage: null,
    }],
  })

  assert.deepEqual(presentation.suiteMetadata[0], {
    suiteExecutionId: 'suite-execution-1',
    source: 'Not returned by this response',
    issuer: 'Not returned by this response',
    signingKey: 'Not returned by this response',
    signer: 'Not returned by this response',
    effectiveExpiry: 'Not returned by this response',
    reviewer: 'Not returned by this response',
    reviewedAt: 'Not returned by this response',
    admissionReasons: [],
    freshnessEvaluatedAt: '2026-08-09T00:00:00+00:00',
    freshnessEffectiveAt: '2026-08-08T00:00:00+00:00',
    expiringAt: '2026-08-30T00:00:00+00:00',
    freshnessReasonCodes: [],
    decisionEvidenceEligible: 'Eligible',
    resultAuthority: 'Verified',
    evidenceResult: 'Passed',
    evidenceResultTone: 'standard',
    admission: 'Verified',
    freshness: 'Current',
    review: 'Accepted',
    limitations: [],
  })
})

test('shows only authoritative trust metadata returned with a suite execution', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'review',
    suiteExecutions: [{
      id: 'suite-execution-1',
      suiteVersionId: 'suite-version-1',
      ownerScope: 'organization',
      ordinal: 1,
      technicalStatus: 'succeeded',
      evidenceResultStatus: 'passed',
      admissionStatus: 'superseded',
      reviewStatus: 'accepted',
      freshnessStatus: 'superseded',
      recordedFreshnessStatus: 'superseded',
      freshnessContractVersion: '1.0.0',
      freshnessEvaluatedAt: '2026-08-09T00:00:00+00:00',
      freshnessEffectiveAt: '2026-08-09T00:00:00+00:00',
      expiringAt: '2026-08-30T00:00:00+00:00',
      freshnessReasonCodes: ['recorded_superseded'],
      decisionEvidenceEligible: false,
      limitations: [],
      failureCode: null,
      failureMessage: null,
      evidenceTrust: {
        sourceType: 'external_provider',
        issuerKey: 'issuer:assurance-lab',
        signingKeyId: 'key-2026-08',
        signerKeyId: 'key-2026-08',
        signerAlgorithm: 'Ed25519',
        effectiveExpiresAt: '2026-08-30T00:00:00+00:00',
        reviewedBy: 'reviewer-1',
        reviewedAt: '2026-08-09T00:00:00+00:00',
        admissionReasons: ['newer passport revision recorded'],
      },
    }],
  })

  assert.deepEqual(presentation.suiteMetadata[0], {
    suiteExecutionId: 'suite-execution-1',
    source: 'external_provider',
    issuer: 'issuer:assurance-lab',
    signingKey: 'key-2026-08',
    signer: 'key-2026-08 (Ed25519)',
    effectiveExpiry: '2026-08-30T00:00:00+00:00',
    reviewer: 'reviewer-1',
    reviewedAt: '2026-08-09T00:00:00+00:00',
    admissionReasons: ['newer passport revision recorded'],
    freshnessEvaluatedAt: '2026-08-09T00:00:00+00:00',
    freshnessEffectiveAt: '2026-08-09T00:00:00+00:00',
    expiringAt: '2026-08-30T00:00:00+00:00',
    freshnessReasonCodes: ['recorded_superseded'],
    decisionEvidenceEligible: 'Not eligible',
    resultAuthority: 'Not established',
    evidenceResult: 'Passed',
    evidenceResultTone: 'neutral',
    admission: 'Superseded',
    freshness: 'Superseded',
    review: 'Accepted',
    limitations: [],
  })
})

test('keeps returned string limitations visible with the suite evidence metadata', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed_with_limitations',
    overallVerdict: 'review',
    suiteExecutions: [{
      id: 'suite-execution-1',
      suiteVersionId: 'suite-version-1',
      ownerScope: 'organization',
      ordinal: 1,
      technicalStatus: 'succeeded',
      evidenceResultStatus: 'passed_with_limitations',
      admissionStatus: 'verified',
      reviewStatus: 'pending',
      freshnessStatus: 'current',
      ...currentFreshness,
      limitations: ['The protected-group coverage is incomplete.'],
      failureCode: null,
      failureMessage: null,
    }],
  })

  assert.deepEqual(presentation.suiteMetadata[0]?.limitations, [
    'The protected-group coverage is incomplete.',
  ])
})

test('surfaces the immutable scope, target, execution, and suite bindings', () => {
  const presentation = buildEvidenceTrustPresentation({
    id: 'run-1',
    organizationId: 'org-1',
    workspaceId: 'workspace-1',
    systemId: 'system-1',
    planId: 'plan-1',
    envelopeId: 'envelope-1',
    lifecyclePhase: 'pre_deploy',
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'review',
    envelope: {
      planContentHash: 'plan-hash',
      executionDepth: 'hybrid',
      enforcementMode: 'human_approval',
      deliveryMode: 'fairmind_worker',
      trustPolicy: { id: 'trust-1', policyHash: 'trust-hash' },
      target: {
        id: 'target-1',
        targetKind: 'vision_model',
        version: '2027.1',
        subjectDigest: 'subject-digest',
        manifestDigest: 'manifest-digest',
      },
      suites: [{
        suiteExecutionId: 'suite-execution-1',
        suiteVersionId: 'suite-version-1',
        manifestDigest: 'suite-manifest-digest',
        adapterName: 'inspect',
        adapterVersion: '0.3.0',
        runnerImageDigest: 'runner-digest',
        configurationHash: 'configuration-hash',
      }],
    },
  })

  assert.deepEqual(presentation.binding.scope.map((item) => item.value), [
    'org-1', 'workspace-1', 'system-1', 'plan-1', 'run-1', 'envelope-1',
  ])
  assert.equal(presentation.binding.execution[0]?.value, 'plan-hash')
  assert.equal(presentation.binding.target[0]?.value, 'target-1')
  assert.deepEqual(presentation.binding.suites[0], {
    suiteExecutionId: 'suite-execution-1',
    suiteVersionId: 'suite-version-1',
    manifestDigest: 'suite-manifest-digest',
    evaluator: 'inspect @ 0.3.0',
    runnerImageDigest: 'runner-digest',
    configurationHash: 'configuration-hash',
    passportRevisionId: 'Not returned by this response',
    signer: 'Not returned by this response',
  })
})

test('does not turn missing envelope fields into positive trust claims', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'awaiting_evidence',
    evidenceOutcome: 'pending',
    overallVerdict: 'insufficient',
    envelope: {},
  })

  assert.equal(presentation.binding.target[0]?.value, 'Not returned by this response')
  assert.equal(presentation.binding.execution[0]?.value, 'Not returned by this response')
  assert.deepEqual(presentation.binding.suites, [])
})

test('derives no unverified-import warning for verified evidence', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'review',
    suiteExecutions: [suiteExecution({
      evidenceTrust: {
        sourceType: 'external_provider',
        issuerKey: 'issuer:assurance-lab',
        signingKeyId: 'key-2026-08',
        signerKeyId: 'key-2026-08',
        signerAlgorithm: 'Ed25519',
        effectiveExpiresAt: '2026-08-30T00:00:00+00:00',
        reviewedBy: 'reviewer-1',
        reviewedAt: '2026-08-09T00:00:00+00:00',
        admissionReasons: [],
      },
    })],
  })

  assert.deepEqual(presentation.evidenceTrustWarnings, {
    hasUnverifiedImportedMaterial: false,
    unverifiedImportedSuites: [],
    hasInconsistentEvidenceTrust: false,
    inconsistentEvidenceSuites: [],
  })
  assert.equal(presentation.suiteMetadata[0]?.resultAuthority, 'Verified')
  assert.equal(presentation.suiteMetadata[0]?.evidenceResultTone, 'standard')
})

test('marks an unverified imported passed result as claimed, human-review-only material', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'approved',
    suiteExecutions: [suiteExecution({
      id: 'unverified-import-1',
      suiteVersionId: 'bias-audit-2026.08',
      admissionStatus: 'unverified',
      decisionEvidenceEligible: true,
      evidenceTrust: {
        sourceType: 'imported_report',
        issuerKey: null,
        signingKeyId: null,
        signerKeyId: null,
        signerAlgorithm: null,
        effectiveExpiresAt: null,
        reviewedBy: null,
        reviewedAt: null,
        admissionReasons: ['unsigned imported report'],
      },
    })],
  })

  assert.deepEqual(presentation.evidenceTrustWarnings, {
    hasUnverifiedImportedMaterial: true,
    unverifiedImportedSuites: [{
      suiteExecutionId: 'unverified-import-1',
      suiteVersionId: 'bias-audit-2026.08',
    }],
    hasInconsistentEvidenceTrust: false,
    inconsistentEvidenceSuites: [],
  })
  assert.equal(presentation.suiteMetadata[0]?.resultAuthority, 'Claimed')
  assert.equal(presentation.suiteMetadata[0]?.decisionEvidenceEligible, 'Not eligible')
  assert.equal(presentation.suiteMetadata[0]?.evidenceResult, 'Claimed result: Passed')
  assert.equal(presentation.suiteMetadata[0]?.evidenceResultTone, 'warning')
  assert.deepEqual(presentation.axes[1], {
    label: 'Evaluator evidence result',
    value: 'Claimed result: Passed',
    tone: 'warning',
  })
  assert.deepEqual(presentation.axes[2], {
    label: 'Governance verdict',
    value: 'Recorded verdict: Approved',
    tone: 'warning',
  })
})

test('alerts conservatively when unverified evidence has a non-imported source', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'review',
    suiteExecutions: [suiteExecution({
      id: 'malformed-unverified-source-1',
      suiteVersionId: 'suite-unexpected-source',
      admissionStatus: 'unverified',
      decisionEvidenceEligible: true,
      evidenceTrust: {
        sourceType: 'external_provider',
        issuerKey: 'issuer:unexpected',
        signingKeyId: 'key-unexpected',
        signerKeyId: 'key-unexpected',
        signerAlgorithm: 'Ed25519',
        effectiveExpiresAt: null,
        reviewedBy: null,
        reviewedAt: null,
        admissionReasons: [],
      },
    })],
  })

  assert.deepEqual(presentation.evidenceTrustWarnings, {
    hasUnverifiedImportedMaterial: false,
    unverifiedImportedSuites: [],
    hasInconsistentEvidenceTrust: true,
    inconsistentEvidenceSuites: [{
      suiteExecutionId: 'malformed-unverified-source-1',
      suiteVersionId: 'suite-unexpected-source',
    }],
  })
  assert.equal(presentation.suiteMetadata[0]?.resultAuthority, 'Claimed')
  assert.equal(presentation.suiteMetadata[0]?.decisionEvidenceEligible, 'Not eligible')
  assert.equal(presentation.suiteMetadata[0]?.evidenceResultTone, 'warning')
})

test('keeps verified suites distinct while identifying the affected unverified import in a mixed run', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed',
    overallVerdict: 'review',
    suiteExecutions: [
      suiteExecution({ id: 'verified-suite', suiteVersionId: 'verified-suite-version' }),
      suiteExecution({
        id: 'unverified-import-suite',
        suiteVersionId: 'imported-suite-version',
        ordinal: 2,
        admissionStatus: 'unverified',
        decisionEvidenceEligible: false,
        evidenceTrust: {
          sourceType: 'imported_report',
          issuerKey: null,
          signingKeyId: null,
          signerKeyId: null,
          signerAlgorithm: null,
          effectiveExpiresAt: null,
          reviewedBy: null,
          reviewedAt: null,
          admissionReasons: [],
        },
      }),
    ],
  })

  assert.deepEqual(
    presentation.evidenceTrustWarnings.unverifiedImportedSuites.map((suite) => suite.suiteExecutionId),
    ['unverified-import-suite'],
  )
  assert.equal(presentation.suiteMetadata[0]?.resultAuthority, 'Verified')
  assert.equal(presentation.suiteMetadata[1]?.resultAuthority, 'Claimed')
  assert.deepEqual(presentation.axes[0], { label: 'Execution status', value: 'Succeeded' })
  assert.deepEqual(presentation.axes[1], {
    label: 'Evaluator evidence result',
    value: 'Mixed-authority aggregate: Passed',
    tone: 'warning',
  })
  assert.deepEqual(presentation.axes[2], {
    label: 'Governance verdict',
    value: 'Recorded verdict: Review',
    tone: 'warning',
  })
})

test('does not misattribute a verified failure to the claimed suite in a mixed run', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'failed',
    evidenceOutcome: 'failed',
    overallVerdict: 'review',
    suiteExecutions: [
      suiteExecution({
        id: 'verified-failure',
        suiteVersionId: 'verified-failure-version',
        technicalStatus: 'failed',
        evidenceResultStatus: 'failed',
      }),
      suiteExecution({
        id: 'claimed-pass',
        suiteVersionId: 'claimed-pass-version',
        ordinal: 2,
        admissionStatus: 'unverified',
        decisionEvidenceEligible: false,
        evidenceTrust: {
          sourceType: 'imported_report',
          issuerKey: null,
          signingKeyId: null,
          signerKeyId: null,
          signerAlgorithm: null,
          effectiveExpiresAt: null,
          reviewedBy: null,
          reviewedAt: null,
          admissionReasons: [],
        },
      }),
    ],
  })

  assert.deepEqual(presentation.axes[1], {
    label: 'Evaluator evidence result',
    value: 'Mixed-authority aggregate: Failed',
    tone: 'warning',
  })
  assert.notEqual(presentation.axes[1]?.value, 'Claimed result: Failed')
  assert.equal(presentation.suiteMetadata[0]?.resultAuthority, 'Verified')
  assert.equal(presentation.suiteMetadata[0]?.evidenceResult, 'Failed')
  assert.equal(presentation.suiteMetadata[1]?.resultAuthority, 'Claimed')
  assert.equal(presentation.suiteMetadata[1]?.evidenceResult, 'Claimed result: Passed')
})

test('keeps a claimed failure visibly mixed when verified evidence passed', () => {
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'failed',
    evidenceOutcome: 'failed',
    overallVerdict: 'review',
    suiteExecutions: [
      suiteExecution({ id: 'verified-pass' }),
      suiteExecution({
        id: 'claimed-failure',
        ordinal: 2,
        technicalStatus: 'failed',
        evidenceResultStatus: 'failed',
        admissionStatus: 'unverified',
        decisionEvidenceEligible: false,
        evidenceTrust: {
          sourceType: 'imported_report',
          issuerKey: null,
          signingKeyId: null,
          signerKeyId: null,
          signerAlgorithm: null,
          effectiveExpiresAt: null,
          reviewedBy: null,
          reviewedAt: null,
          admissionReasons: [],
        },
      }),
    ],
  })

  assert.deepEqual(presentation.axes[1], {
    label: 'Evaluator evidence result',
    value: 'Mixed-authority aggregate: Failed',
    tone: 'warning',
  })
})

test('preserves long limitations for wrapping rather than omitting them', () => {
  const limitation = 'This imported source limitation is intentionally very long so the presentation layer must retain the complete human-review context without truncating the explanation into an unsafe trust shortcut.'.repeat(3)
  const presentation = buildEvidenceTrustPresentation({
    technicalStatus: 'succeeded',
    evidenceOutcome: 'passed_with_limitations',
    overallVerdict: 'review',
    suiteExecutions: [suiteExecution({
      admissionStatus: 'unverified',
      decisionEvidenceEligible: false,
      evidenceTrust: {
        sourceType: 'imported_report',
        issuerKey: null,
        signingKeyId: null,
        signerKeyId: null,
        signerAlgorithm: null,
        effectiveExpiresAt: null,
        reviewedBy: null,
        reviewedAt: null,
        admissionReasons: [],
      },
      limitations: [limitation],
    })],
  })

  assert.deepEqual(presentation.suiteMetadata[0]?.limitations, [limitation])
})
