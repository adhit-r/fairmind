# FairMind-E Expert-Panel Answer Key (M6)

Expected engine labels for the twelve panel profiles. Keep this file separate
from `PROFILES.md`; raters must not see it before submitting ratings. Every
label below is validated against the production domain engine
(`apps/backend/src/domain/environmental`) by `generate_profiles.py --validate`
and `tests/test_profiles.py`.

## Overview

| ID | Matrix cell | Provenance | Confidence | Band | Tier | Recommendation | Blocking |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| P01 | low+measured | measured | 0.93 | measured | low | go | false |
| P02 | low+estimated | vendor_reported | 0.50 | estimated | low | go | false |
| P03 | low+unknown | manual | 0.30 | unknown | low | conditional_go | true |
| P04 | medium+measured | measured | 0.93 | measured | medium | conditional_go | false |
| P05 | medium+estimated | vendor_reported | 0.50 | estimated | medium | conditional_go | false |
| P06 | medium+unknown | manual | 0.30 | unknown | medium | no_go | true |
| P07 | high+measured | measured | 0.93 | measured | high | conditional_go | false |
| P08 | high+estimated | vendor_reported | 0.50 | estimated | high | no_go | true |
| P09 | high+unknown | unknown | 0.00 | unknown | high | no_go | true |
| P10 | low+unknown | manual | 0.30 | unknown | low | conditional_go | false |
| P11 | high+measured | measured | 0.93 | measured | high | conditional_go | false |
| P12 | medium+estimated | vendor_reported | 0.50 | estimated | medium | conditional_go | true |

Matrix coverage: all nine impact x confidence cells appear once; the
conditional_go boundary cells adjacent to no_go (low+unknown via P03/P10 and
high+measured via P07/P11) and medium+estimated (P05/P12) each appear twice.
Within each doubled cell the two profiles deliberately differ in mitigation or
exception state so that approval blocking varies while the recommendation does
not.

## P01: KisanScore agri-credit risk model retraining

- Matrix cell: low+measured
- Expected recommendation: go
- Expected risk tier: low
- Expected confidence: 0.93 (measured band, provenance measured)
- Expected approval blocking: false
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 missing | ENV-5 present | ENV-6 present
- Coverage rate: 0.8333
- Mitigation design: Go cell: no mitigation required; approval is not blocking.

Metered PDU and RAPL evidence yields a 0.93 confidence score in the measured band, and 38.3 kgCO2e for a classical training run sits well inside the low tier. The (low, measured) cell resolves to go with nothing to block approval. ENV-4 is missing only because a per-request efficiency figure does not apply to a training-run functional unit.

## P02: LexRetrieve statute and case-law RAG search

- Matrix cell: low+estimated
- Expected recommendation: go
- Expected risk tier: low
- Expected confidence: 0.50 (estimated band, provenance vendor_reported)
- Expected approval blocking: false
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 present | ENV-5 present | ENV-6 present
- Coverage rate: 1
- Mitigation design: Go cell: no mitigation required; approval is not blocking.

Provider-reported figures sit in the vendor_reported class, 0.50 in the estimated band, and 0.0004 kgCO2e per 1000 requests is comfortably low impact. The (low, estimated) cell resolves to go, and the profile carries full ENV-1..6 coverage.

## P03: TalentSift resume screening ranker

- Matrix cell: low+unknown
- Expected recommendation: conditional_go
- Expected risk tier: low
- Expected confidence: 0.30 (unknown band, provenance manual)
- Expected approval blocking: true
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 missing | ENV-4 present | ENV-5 present | ENV-6 missing
- Coverage rate: 0.6667
- Mitigation design: Conditional_go deliberately left without a dated mitigation or exception: approval_blocking is true (contrast with P10).

A manual FLOP worksheet caps evidence at 0.30, inside the unknown band, while impact stays low, so the (low, unknown) cell returns conditional_go. With no dated mitigation and no exception the release is approval-blocking. The missing market-based figure also leaves ENV-3 uncovered.

## P04: TriageAssist clinical intake fine-tune

- Matrix cell: medium+measured
- Expected recommendation: conditional_go
- Expected risk tier: medium
- Expected confidence: 0.93 (measured band, provenance measured)
- Expected approval blocking: false
- Dated mitigation: true
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 missing | ENV-5 present | ENV-6 present
- Coverage rate: 0.8333
- Mitigation design: Dated mitigation documented: approval_blocking is false.

Metered fine-tune evidence scores 0.93 in the measured band and 1350 kgCO2e sits mid-range in the medium tier, so the (medium, measured) cell returns conditional_go. The dated solar-PPA migration plan documents mitigation, so the conditional release is not approval-blocking.

## P05: UPI fraud scoring service

- Matrix cell: medium+estimated
- Expected recommendation: conditional_go
- Expected risk tier: medium
- Expected confidence: 0.50 (estimated band, provenance vendor_reported)
- Expected approval blocking: false
- Dated mitigation: true
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 missing | ENV-3 present | ENV-4 present | ENV-5 present | ENV-6 present
- Coverage rate: 0.8333
- Mitigation design: Dated mitigation documented: approval_blocking is false (contrast with P12).

Vendor-reported dashboard evidence is fixed at 0.50, the vendor_reported midpoint, whatever score the submitter attaches, landing in the estimated band, while 0.0038 kgCO2e per 1000 requests is medium impact. The (medium, estimated) cell returns conditional_go and the dated hydro-region migration keeps it from blocking approval. The undisclosed kilowatt-hours leave ENV-2 uncovered.

## P06: Workspace chat assistant serving

- Matrix cell: medium+unknown
- Expected recommendation: no_go
- Expected risk tier: medium
- Expected confidence: 0.30 (unknown band, provenance manual)
- Expected approval blocking: true
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 present | ENV-5 present | ENV-6 present
- Coverage rate: 1
- Mitigation design: No_go cell: approval_blocking is true regardless of mitigation.

The manual estimate scores 0.30, in the unknown band, while 4.6 kgCO2e per million tokens is medium impact, so the (medium, unknown) cell returns no_go. Full ENV-1..6 coverage cannot rescue evidence that is too weak for a medium-impact release, and a no_go always blocks approval.

## P07: Biomedical domain LLM pretraining run

- Matrix cell: high+measured
- Expected recommendation: conditional_go
- Expected risk tier: high
- Expected confidence: 0.93 (measured band, provenance measured)
- Expected approval blocking: false
- Dated mitigation: true
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 missing | ENV-5 present | ENV-6 present
- Coverage rate: 0.8333
- Mitigation design: Dated mitigation documented: approval_blocking is false (contrast with the P11 exception path in the same cell).

IPMI-metered training evidence scores 0.93 in the measured band and 62,320 kgCO2e is high impact, so the (high, measured) cell returns conditional_go. The dated scheduling and energy-budget plan documents mitigation, so approval is not blocked.

## P08: Indic multilingual LLM continued pretraining

- Matrix cell: high+estimated
- Expected recommendation: no_go
- Expected risk tier: high
- Expected confidence: 0.50 (estimated band, provenance vendor_reported)
- Expected approval blocking: true
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 missing | ENV-5 present | ENV-6 present
- Coverage rate: 0.8333
- Mitigation design: No_go cell: approval_blocking is true; disclosed offsets deliberately do not rescue the gate.

The provider-reported figure is vendor_reported, 0.50 in the estimated band, and 28,623 kgCO2e is high impact, so the (high, estimated) cell returns no_go. Retired carbon units are disclosed but never improve confidence, tier, or the gate, and the absence of a dated mitigation is moot for a no_go, which always blocks approval.

## P09: Third-party document-intelligence API

- Matrix cell: high+unknown
- Expected recommendation: no_go
- Expected risk tier: high
- Expected confidence: 0.00 (unknown band, provenance unknown)
- Expected approval blocking: true
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 missing | ENV-3 missing | ENV-4 present | ENV-5 missing | ENV-6 present
- Coverage rate: 0.5
- Mitigation design: No_go cell: approval_blocking is true; undisclosed provenance forces confidence 0.0.

The vendor discloses nothing, so provenance is unknown and confidence is forced to 0.0, which returns no_go before any matrix lookup. The worst-case screening figure of 18 kgCO2e per million generated tokens tiers the workload high, but the undisclosed evidence drives the label. Coverage exists only for the boundary, the efficiency figure, and the vacuously satisfied mitigation control.

## P10: Digital lending pre-qualification scorer

- Matrix cell: low+unknown
- Expected recommendation: conditional_go
- Expected risk tier: low
- Expected confidence: 0.30 (unknown band, provenance manual)
- Expected approval blocking: false
- Dated mitigation: true
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 present | ENV-5 present | ENV-6 present
- Coverage rate: 1
- Mitigation design: Dated evidence-improvement mitigation documented: approval_blocking is false (contrast with P03).

A documented manual worksheet scores 0.30, in the unknown band, with low impact, so the (low, unknown) cell returns conditional_go. Unlike P03, the dated CodeCarbon instrumentation commitment documents mitigation, so the conditional release is not approval-blocking.

## P11: Marketplace search re-ranking LLM serving

- Matrix cell: high+measured
- Expected recommendation: conditional_go
- Expected risk tier: high
- Expected confidence: 0.93 (measured band, provenance measured)
- Expected approval blocking: false
- Dated mitigation: false
- Owned exception: true
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 present | ENV-5 present | ENV-6 present
- Coverage rate: 1
- Mitigation design: Owned exception instead of a dated mitigation: approval_blocking is false via the exception path (contrast with P07).

Fully metered serving evidence scores 0.93 in the measured band and 14.5 kgCO2e per million tokens is high impact, so the (high, measured) cell returns conditional_go. There is no dated mitigation, but the signed exception with owner, expiry, and rationale satisfies the gate, so approval is not blocked.

## P12: Enterprise semantic embedding pipeline

- Matrix cell: medium+estimated
- Expected recommendation: conditional_go
- Expected risk tier: medium
- Expected confidence: 0.50 (estimated band, provenance vendor_reported)
- Expected approval blocking: true
- Dated mitigation: false
- Owned exception: false
- Control coverage: ENV-1 present | ENV-2 present | ENV-3 present | ENV-4 present | ENV-5 present | ENV-6 missing
- Coverage rate: 0.8333
- Mitigation design: Conditional_go with undated intentions only: approval_blocking is true (contrast with P05).

Provider-published per-request figures are vendor_reported, 0.50 in the estimated band, and 0.004 kgCO2e per 1000 requests is medium impact, so the (medium, estimated) cell returns conditional_go. The batching and distillation ideas carry no owner or date and no exception was requested, so the release is approval-blocking, unlike P05.
