export type LegacyEvaluationFeatureGates = {
  legacyEvidenceLinking: boolean
}

type LegacyEvaluationFeatureGateEnvironment = {
  legacyEvidenceLinking?: string
}

export function resolveLegacyEvaluationFeatureGates(
  environment: LegacyEvaluationFeatureGateEnvironment,
): LegacyEvaluationFeatureGates {
  void environment
  return {
    legacyEvidenceLinking: false,
  }
}

export function allowedLegacyEnforcementModes() {
  return ['advisory', 'human_approval'] as const
}

export function allowedLegacyDeliveryModes() {
  return ['external_provider', 'imported_report'] as const
}
