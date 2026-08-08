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
    signingKeyRevocationReason: string | null
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
  axes: Array<{ label: string; value: string }>
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
    signingKeyRevocationReason: string
    evidenceResult: string
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

export function sentenceLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/^./, (character) => character.toUpperCase())
}

export function buildEvidenceTrustPresentation(input: EvidenceTrustInput): EvidenceTrustPresentation {
  const envelope = record(input.envelope)
  const target = record(envelope.target)
  const trustPolicy = record(envelope.trustPolicy)
  const envelopeSuites = Array.isArray(envelope.suites) ? envelope.suites : []
  const executionsById = new Map((input.suiteExecutions ?? []).map((suite) => [suite.id, suite]))

  return {
    axes: [
      { label: 'Execution status', value: sentenceLabel(input.technicalStatus) },
      { label: 'Evaluator evidence result', value: sentenceLabel(input.evidenceOutcome) },
      { label: 'Governance verdict', value: sentenceLabel(input.overallVerdict) },
    ],
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
    suiteMetadata: (input.suiteExecutions ?? []).map((suite) => ({
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
      signingKeyRevocationReason: text(suite.evidenceTrust?.signingKeyRevocationReason),
      evidenceResult: sentenceLabel(suite.evidenceResultStatus),
      admission: sentenceLabel(suite.admissionStatus),
      freshness: sentenceLabel(suite.freshnessStatus),
      review: sentenceLabel(suite.reviewStatus),
      limitations: suite.limitations.filter(
        (limitation): limitation is string => typeof limitation === 'string' && limitation.trim().length > 0,
      ),
    })),
  }
}
