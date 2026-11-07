export type LegacyEvaluationFeatureGates = {
  legacyEvidenceLinking: boolean
}

type LegacyEvaluationFeatureGateEnvironment = {
  legacyEvidenceLinking?: string
}

const explicitlyEnabled = (value: string | undefined) => value === 'true'

export function resolveLegacyEvaluationFeatureGates(
  environment: LegacyEvaluationFeatureGateEnvironment,
): LegacyEvaluationFeatureGates {
  return {
    legacyEvidenceLinking: explicitlyEnabled(environment.legacyEvidenceLinking),
  }
}

export const legacyEvaluationFeatureGates = resolveLegacyEvaluationFeatureGates({
  legacyEvidenceLinking: process.env.NEXT_PUBLIC_FAIRMIND_ASSURANCE_LEGACY_EVIDENCE_LINKING_ENABLED,
})

export function allowedLegacyEnforcementModes() {
  return ['advisory', 'human_approval'] as const
}

export function allowedLegacyDeliveryModes() {
  return ['external_provider', 'imported_report'] as const
}
