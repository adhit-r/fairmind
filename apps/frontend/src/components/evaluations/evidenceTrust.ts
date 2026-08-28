export type EvidenceTrustSuiteInput = {
  id: string
  suiteVersionId: string
  ownerScope: string
  ordinal: number
  technicalStatus: string
  evidenceResultStatus: string
  admissionStatus: string
  reviewStatus: string
  freshnessStatus: string
  recordedFreshnessStatus: string | null
  freshnessContractVersion: '1.0.0' | null
  freshnessEvaluatedAt: string | null
  freshnessEffectiveAt: string | null
  expiringAt: string | null
  freshnessReasonCodes: string[] | null
  decisionEvidenceEligible: boolean | null
  evidenceTrust?: {
    sourceType: string | null
    issuerKey: string | null
    signingKeyId: string | null
    signerKeyId: string | null
    signerAlgorithm: string | null
    effectiveExpiresAt: string | null
    reviewedBy: string | null
    reviewedAt: string | null
    admissionReasons: string[] | null
  } | null
  limitations: unknown[]
  failureCode: string | null
  failureMessage: string | null
}

export type EvidenceTrustInput = {
  id?: string
  organizationId?: string
  workspaceId?: string
  systemId?: string
  planId?: string
  lifecyclePhase?: string
  envelopeId?: string
  envelope?: unknown
  technicalStatus: string
  evidenceOutcome: string
  overallVerdict: string
  suiteExecutions?: EvidenceTrustSuiteInput[]
}

export type EvidenceTrustPresentation = {
  axes: Array<{
    label: string
    value: string
    tone?: 'warning'
  }>
  evidenceTrustWarnings: {
    hasUnverifiedImportedMaterial: boolean
    unverifiedImportedSuites: Array<{
      suiteExecutionId: string
      suiteVersionId: string
    }>
    hasInconsistentEvidenceTrust: boolean
    inconsistentEvidenceSuites: Array<{
      suiteExecutionId: string
      suiteVersionId: string
    }>
  }
  binding: {
    scope: Array<{ label: string; value: string }>
    execution: Array<{ label: string; value: string }>
    target: Array<{ label: string; value: string }>
    suites: Array<{
      suiteExecutionId: string
      suiteVersionId: string
      manifestDigest: string
      evaluator: string
      runnerImageDigest: string
      configurationHash: string
      passportRevisionId: string
      signer: string
    }>
  }
  suiteMetadata: Array<{
    suiteExecutionId: string
    source: string
    issuer: string
    signingKey: string
    signer: string
    effectiveExpiry: string
    reviewer: string
    reviewedAt: string
    admissionReasons: string[]
    freshnessEvaluatedAt: string
    freshnessEffectiveAt: string
    expiringAt: string
    freshnessReasonCodes: string[]
    decisionEvidenceEligible: string
    resultAuthority: 'Verified' | 'Claimed' | 'Not established'
    evidenceResult: string
    evidenceResultTone: 'standard' | 'warning' | 'neutral'
    admission: string
    freshness: string
    review: string
    limitations: string[]
  }>
}

const NOT_RETURNED = 'Not returned by this response'

function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {}
}

function text(value: unknown) {
  return typeof value === 'string' && value.trim().length > 0 ? value : NOT_RETURNED
}

function row(label: string, value: unknown) {
  return { label, value: text(value) }
}

function signer(value: EvidenceTrustSuiteInput['evidenceTrust']) {
  const keyId = text(value?.signerKeyId)
  const algorithm = text(value?.signerAlgorithm)
  return keyId === NOT_RETURNED && algorithm === NOT_RETURNED
    ? NOT_RETURNED
    : `${keyId} (${algorithm})`
}

function reasons(value: EvidenceTrustSuiteInput['evidenceTrust']) {
  return (value?.admissionReasons ?? []).filter(
    (reason): reason is string => typeof reason === 'string' && reason.trim().length > 0,
  )
}

function sourceType(suite: EvidenceTrustSuiteInput) {
  return typeof suite.evidenceTrust?.sourceType === 'string'
    ? suite.evidenceTrust.sourceType
    : ''
}

function isUnverifiedImportedMaterial(suite: EvidenceTrustSuiteInput) {
  return suite.admissionStatus === 'unverified' && sourceType(suite) === 'imported_report'
}

function hasInconsistentEvidenceTrust(suite: EvidenceTrustSuiteInput) {
  const source = sourceType(suite)
  return (suite.admissionStatus === 'unverified' && source !== 'imported_report')
    || (source === 'imported_report' && suite.admissionStatus !== 'unverified')
}

function claimedResultAuthority(suite: EvidenceTrustSuiteInput) {
  return suite.admissionStatus === 'unverified' || sourceType(suite) === 'imported_report'
}

function resultAuthority(suite: EvidenceTrustSuiteInput): 'Verified' | 'Claimed' | 'Not established' {
  if (claimedResultAuthority(suite)) return 'Claimed'
  if (suite.admissionStatus === 'verified') return 'Verified'
  return 'Not established'
}

function warningSuite(suite: EvidenceTrustSuiteInput) {
  return {
    suiteExecutionId: text(suite.id),
    suiteVersionId: text(suite.suiteVersionId),
  }
}

export function sentenceLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/^./, (character) => character.toUpperCase())
}

export function buildEvidenceTrustPresentation(input: EvidenceTrustInput): EvidenceTrustPresentation {
  const envelope = record(input.envelope)
  const target = record(envelope.target)
  const trustPolicy = record(envelope.trustPolicy)
  const envelopeSuites = Array.isArray(envelope.suites) ? envelope.suites : []
  const suiteExecutions = input.suiteExecutions ?? []
  const executionsById = new Map(suiteExecutions.map((suite) => [suite.id, suite]))
  const unverifiedImportedSuites = suiteExecutions
    .filter(isUnverifiedImportedMaterial)
    .map(warningSuite)
  const inconsistentEvidenceSuites = suiteExecutions
    .filter(hasInconsistentEvidenceTrust)
    .map(warningSuite)
  const evaluatorEvidenceResult = sentenceLabel(input.evidenceOutcome)
  const governanceVerdict = sentenceLabel(input.overallVerdict)
  const hasClaimedEvaluatorMaterial = unverifiedImportedSuites.length > 0
    || inconsistentEvidenceSuites.length > 0
  const allEvaluatorMaterialIsClaimed = suiteExecutions.length > 0
    && suiteExecutions.every((suite) => claimedResultAuthority(suite))

  return {
    axes: [
      { label: 'Execution status', value: sentenceLabel(input.technicalStatus) },
      {
        label: 'Evaluator evidence result',
        value: hasClaimedEvaluatorMaterial
          ? allEvaluatorMaterialIsClaimed
            ? `Claimed result: ${evaluatorEvidenceResult}`
            : `Mixed-authority aggregate: ${evaluatorEvidenceResult}`
          : evaluatorEvidenceResult,
        ...(hasClaimedEvaluatorMaterial ? { tone: 'warning' as const } : {}),
      },
      {
        label: 'Governance verdict',
        value: hasClaimedEvaluatorMaterial
          ? `Recorded verdict: ${governanceVerdict}`
          : governanceVerdict,
        ...(hasClaimedEvaluatorMaterial ? { tone: 'warning' as const } : {}),
      },
    ],
    evidenceTrustWarnings: {
      hasUnverifiedImportedMaterial: unverifiedImportedSuites.length > 0,
      unverifiedImportedSuites,
      hasInconsistentEvidenceTrust: inconsistentEvidenceSuites.length > 0,
      inconsistentEvidenceSuites,
    },
    binding: {
      scope: [
        row('Organization', input.organizationId),
        row('Workspace', input.workspaceId),
        row('AI system', input.systemId),
        row('Plan', input.planId),
        row('Run', input.id),
        row('Envelope', input.envelopeId ?? envelope.envelopeId),
      ],
      execution: [
        row('Plan content hash', envelope.planContentHash),
        row('Lifecycle phase', input.lifecyclePhase ?? envelope.lifecyclePhase),
        row('Execution depth', envelope.executionDepth),
        row('Enforcement mode', envelope.enforcementMode),
        row('Delivery source', envelope.deliveryMode),
        row('Trust policy', trustPolicy.id),
        row('Trust policy hash', trustPolicy.policyHash),
      ],
      target: [
        row('Target version', target.id),
        row('Target kind', target.targetKind),
        row('Target version label', target.version),
        row('Subject digest', target.subjectDigest),
        row('Manifest digest', target.manifestDigest),
      ],
      suites: envelopeSuites.map((suiteValue) => {
        const suite = record(suiteValue)
        const execution = executionsById.get(text(suite.suiteExecutionId))
        const adapterName = text(suite.adapterName)
        const adapterVersion = text(suite.adapterVersion)
        return {
          suiteExecutionId: text(suite.suiteExecutionId),
          suiteVersionId: text(suite.suiteVersionId),
          manifestDigest: text(suite.manifestDigest),
          evaluator: adapterName === NOT_RETURNED && adapterVersion === NOT_RETURNED
            ? NOT_RETURNED
            : `${adapterName} @ ${adapterVersion}`,
          runnerImageDigest: text(suite.runnerImageDigest),
          configurationHash: text(suite.configurationHash),
          passportRevisionId: NOT_RETURNED,
          signer: signer(execution?.evidenceTrust),
        }
      }),
    },
    suiteMetadata: suiteExecutions.map((suite) => {
      const authority = resultAuthority(suite)
      const result = sentenceLabel(suite.evidenceResultStatus)
      return {
      suiteExecutionId: suite.id,
      // ownerScope describes suite ownership, not the source of this evidence.
      source: text(suite.evidenceTrust?.sourceType),
      issuer: text(suite.evidenceTrust?.issuerKey),
      signingKey: text(suite.evidenceTrust?.signingKeyId),
      signer: signer(suite.evidenceTrust),
      effectiveExpiry: text(suite.evidenceTrust?.effectiveExpiresAt),
      reviewer: text(suite.evidenceTrust?.reviewedBy),
      reviewedAt: text(suite.evidenceTrust?.reviewedAt),
      admissionReasons: reasons(suite.evidenceTrust),
      freshnessEvaluatedAt: text(suite.freshnessEvaluatedAt),
      freshnessEffectiveAt: text(suite.freshnessEffectiveAt),
      expiringAt: text(suite.expiringAt),
      freshnessReasonCodes: (suite.freshnessReasonCodes ?? []).filter(
        (reason): reason is string => typeof reason === 'string' && reason.trim().length > 0,
      ),
      decisionEvidenceEligible: authority === 'Claimed'
        ? 'Not eligible'
        : suite.decisionEvidenceEligible === null
        ? NOT_RETURNED
        : suite.decisionEvidenceEligible ? 'Eligible' : 'Not eligible',
      resultAuthority: authority,
      evidenceResult: authority === 'Claimed' ? `Claimed result: ${result}` : result,
      evidenceResultTone: authority === 'Claimed'
        ? 'warning'
        : authority === 'Verified' ? 'standard' : 'neutral',
      admission: sentenceLabel(suite.admissionStatus),
      freshness: sentenceLabel(suite.freshnessStatus),
      review: sentenceLabel(suite.reviewStatus),
      limitations: suite.limitations.filter(
        (limitation): limitation is string => typeof limitation === 'string' && limitation.trim().length > 0,
      ),
      }
    }),
  }
}
