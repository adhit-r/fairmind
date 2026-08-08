export type LegacyEvaluationFeatureGates = {
  automaticEnforcement: boolean
  fairmindWorkerDelivery: boolean
  legacyEvidenceLinking: boolean
}

type LegacyEvaluationFeatureGateEnvironment = {
  automaticEnforcement?: string
  fairmindWorkerDelivery?: string
  legacyEvidenceLinking?: string
}

const explicitlyEnabled = (value: string | undefined) => value === 'true'

export function resolveLegacyEvaluationFeatureGates(
  environment: LegacyEvaluationFeatureGateEnvironment,
): LegacyEvaluationFeatureGates {
  return {
    automaticEnforcement: explicitlyEnabled(environment.automaticEnforcement),
    fairmindWorkerDelivery: explicitlyEnabled(environment.fairmindWorkerDelivery),
    legacyEvidenceLinking: explicitlyEnabled(environment.legacyEvidenceLinking),
  }
}

export const legacyEvaluationFeatureGates = resolveLegacyEvaluationFeatureGates({
  automaticEnforcement: process.env.NEXT_PUBLIC_FAIRMIND_ASSURANCE_LEGACY_AUTOMATIC_ENFORCEMENT_ENABLED,
  fairmindWorkerDelivery: process.env.NEXT_PUBLIC_FAIRMIND_ASSURANCE_LEGACY_FAIRMIND_WORKER_ENABLED,
  legacyEvidenceLinking: process.env.NEXT_PUBLIC_FAIRMIND_ASSURANCE_LEGACY_EVIDENCE_LINKING_ENABLED,
})

export function allowedLegacyEnforcementModes(gates: LegacyEvaluationFeatureGates) {
  return gates.automaticEnforcement
    ? ['advisory', 'human_approval', 'automatic'] as const
    : ['advisory', 'human_approval'] as const
}

export function allowedLegacyDeliveryModes(gates: LegacyEvaluationFeatureGates) {
  return gates.fairmindWorkerDelivery
    ? ['fairmind_worker', 'external_provider', 'imported_report'] as const
    : ['external_provider', 'imported_report'] as const
}
