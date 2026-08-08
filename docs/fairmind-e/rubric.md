# FairMind-E Environmental Evidence Rubric

This rubric defines how FairMind-E turns environmental impact evidence into confidence, risk tier, and release recommendation. It is intentionally conservative: weak evidence can block release even when the reported emissions number is small.

## Core Invariants

- Provenance is categorical: `measured`, `tool_estimated`, `vendor_reported`, `manual`, or `unknown`.
- Uncertainty is numeric and separate from provenance. Do not merge provenance and uncertainty into one scalar.
- Offsets and renewable energy certificates can be disclosed, but they never improve provenance, uncertainty, confidence, risk tier, or recommendation.
- Carbon must be reported both as location-based and market-based. Scheduling and region-shift claims must declare whether carbon intensity is marginal or average.
- Vendor-reported figures cap confidence at `0.60`.
- Moderate impact with unknown evidence returns `no_go`.

## Provenance Ladder

| Provenance class | Confidence score range | Default confidence | Uncertainty guidance | Evidence examples |
| --- | ---: | ---: | --- | --- |
| `measured` | 0.85-1.00 | 0.95 | Usually 0-10 percent when metering boundary is documented. | Metered power, RAPL/NVML with calibration notes, cloud metered energy feed. |
| `tool_estimated` | 0.60-0.85 | 0.75 | Usually 10-30 percent depending on model, hardware, and regional CI assumptions. | CodeCarbon, EcoLogits, estimator from workload telemetry. |
| `vendor_reported` | 0.40-0.60 | 0.60 | Usually 15-50 percent unless the vendor supplies audited boundary and method details. | Provider carbon report, billing export, cloud sustainability portal. |
| `manual` | 0.20-0.40 | 0.30 | Usually 30-100 percent; assumptions must be explicit. | Spreadsheet estimate, hand-entered GPU hours, assumed utilization. |
| `unknown` | 0.00 | 0.00 | Unknown; do not infer a numeric band unless evidence is collected. | Missing source, undocumented claim, inaccessible vendor metric. |

Confidence can move within the class range when uncertainty is unusually high or evidence boundaries are incomplete, but it cannot cross into a stronger provenance class. A low-uncertainty vendor report remains capped at `0.60`.

## Impact Bands

| Impact level | Typical trigger | Examples |
| --- | --- | --- |
| `low` | Small absolute footprint and at or below the approved baseline. | Cached inference batch, small evaluation run, lower-carbon region without latency or data-residency issue. |
| `moderate` | Material footprint, missing baseline, or 1.0x-2.0x approved baseline intensity. | New recurring batch job, RAG inference with growth risk, moderate training run. |
| `high` | High absolute footprint, greater than 2.0x approved baseline intensity, or known material operational concern. | Transformer fine-tune, large embedding backfill, uncached high-volume inference, region shift to higher CI. |

Projects may calibrate absolute thresholds by business unit, but the gate matrix below is invariant once impact is assigned.

## Gate Matrix

| Confidence band | Low impact | Moderate impact | High impact |
| --- | --- | --- | --- |
| Strong: `confidence_score >= 0.75` | `go` | `conditional_go` | `conditional_go` only with documented mitigations; otherwise `no_go` |
| Moderate: `0.40 <= confidence_score < 0.75` | `conditional_go` | `conditional_go` | `no_go` |
| Weak or unknown: `confidence_score < 0.40` | `conditional_go` | `no_go` | `no_go` |

`conditional_go` requires at least one tracked action: collect stronger evidence, reduce impact, schedule in a lower-carbon window, batch or cache workload, substitute a smaller model, or document an approved exception.

## Risk Tier Mapping

| Recommendation | Default risk tier | Required reviewer posture |
| --- | --- | --- |
| `go` | `low` | Evidence is sufficient for release without environmental exception. |
| `conditional_go` with low impact | `medium` | Release is allowed only with tracked follow-up. |
| `conditional_go` with moderate or high impact | `high` | Release requires mitigation owner and review date. |
| `no_go` | `critical` | Release is blocked until evidence or impact changes, or a formal exception is approved. |

## Canonical Cases

| Case | Expected outcome |
| --- | --- |
| High impact plus measured evidence plus documented mitigations | `risk_tier=high`, `recommendation=conditional_go` |
| Moderate impact plus unknown evidence | `risk_tier=critical`, `recommendation=no_go` |
| Vendor-reported evidence with low uncertainty | `confidence_score <= 0.60` |
| Any offset or REC disclosure | No improvement to confidence, tier, or recommendation |
| Scheduling claim without average/marginal CI basis | Treat as incomplete evidence and require follow-up |

## Exception Path

Exceptions are allowed only as governance records, not as hidden overrides. Each exception must include:

- accountable owner,
- expiry date,
- system and assessment version,
- rationale,
- compensating control or mitigation,
- reviewer state,
- evidence references.

An exception may allow a business release outside the rubric, but it does not change the underlying FairMind-E recommendation. The original `no_go` or `conditional_go` outcome remains part of the audit trail.
