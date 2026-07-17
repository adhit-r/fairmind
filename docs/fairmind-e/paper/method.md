# Method

FairMind-E evaluates one environmental assessment at a time. The assessment declares a lifecycle phase, functional unit, carbon metrics, evidence provenance, uncertainty, mitigation state, and optional exception data.

## Gate Inputs

- `lifecycle_phase`: training, fine-tune, inference, or LLM inference.
- `metrics`: location-based and market-based carbon fields, plus the phase-specific intensity metric.
- `provenance_class`: measured, tool-estimated, vendor-reported, manual, or unknown.
- `confidence_score`: caller-supplied score, capped by provenance.
- `intensity_vs_baseline`: optional ratio that can bump or lower impact tier.
- `mitigation_readiness`: documented, planned, or missing.
- `exception`: owner, expiry, and rationale for conditional releases.

## Decision Logic

1. Normalize provenance and cap confidence.
2. Tier impact using the lifecycle-specific metric.
3. Apply baseline-intensity adjustment.
4. Resolve recommendation from the impact-confidence matrix.
5. Block approval if the recommendation is `no_go`.
6. For `conditional_go`, require documented mitigation or an owned exception.

## Evidence Controls

The ENV-1..6 controls check boundary, energy/carbon, dual carbon basis, intensity, confidence, and mitigation/exception coverage.

## Reproducibility

The paper wedge uses a checked-in fixture set and deterministic evaluator. No network, credentials, or external services are required.
