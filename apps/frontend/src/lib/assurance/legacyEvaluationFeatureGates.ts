export type LegacyEvaluationFeatureGates = {
  fairmindWorkerDelivery: boolean
  legacyEvidenceLinking: boolean
}

type LegacyEvaluationFeatureGateEnvironment = {
  fairmindWorkerDelivery?: string
  legacyEvidenceLinking?: string
}

const explicitlyEnabled = (value: string | undefined) => value === 'true'

export function resolveLegacyEvaluationFeatureGates(
  environment: LegacyEvaluationFeatureGateEnvironment,
): LegacyEvaluationFeatureGates {
  return {
    fairmindWorkerDelivery: explicitlyEnabled(environment.fairmindWorkerDelivery),
    legacyEvidenceLinking: explicitlyEnabled(environment.legacyEvidenceLinking),
  }
}

export const legacyEvaluationFeatureGates = resolveLegacyEvaluationFeatureGates({
  fairmindWorkerDelivery: process.env.NEXT_PUBLIC_FAIRMIND_ASSURANCE_LEGACY_FAIRMIND_WORKER_ENABLED,
  legacyEvidenceLinking: process.env.NEXT_PUBLIC_FAIRMIND_ASSURANCE_LEGACY_EVIDENCE_LINKING_ENABLED,
})

export function allowedLegacyEnforcementModes() {
  return ['advisory', 'human_approval'] as const
}

export function allowedLegacyDeliveryModes(gates: LegacyEvaluationFeatureGates) {
  return gates.fairmindWorkerDelivery
    ? ['fairmind_worker', 'external_provider', 'imported_report'] as const
    : ['external_provider', 'imported_report'] as const
}
