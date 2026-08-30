export interface EvidenceHubFeatureGateEnvironment {
  untrustedExternalEvidenceLinking?: string
}

export interface EvidenceHubFeatureGates {
  untrustedExternalEvidenceLinking: boolean
}

export function resolveEvidenceHubFeatureGates(
  environment: EvidenceHubFeatureGateEnvironment,
): EvidenceHubFeatureGates {
  return {
    untrustedExternalEvidenceLinking:
      environment.untrustedExternalEvidenceLinking === 'true',
  }
}
