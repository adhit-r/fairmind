# FairMind Integration Map

This research package should be presented as a FairMind-grounded artifact, not as a disconnected schema exercise. The fairness evidence profile is the review layer that FairMind can attach to its existing AI BOM, bias detection, evidence collection, monitoring, and compliance surfaces.

## Current FairMind Surfaces

| FairMind surface | File | How it supports the profile |
| --- | --- | --- |
| AI BOM service | `apps/backend/src/application/services/ai_bom_service.py` | Creates AI BOM documents, layers components across data, model development, infrastructure, deployment, monitoring, security, and compliance, and computes risk/compliance summaries. |
| Database-backed AI BOM service | `apps/backend/src/application/services/real_ai_bom_service.py` | Persists AI BOM documents and components through repository-backed database operations. |
| AI BOM route | `apps/backend/api/routes/real_ai_bom.py` | Exposes create, list, retrieve, update, delete, and health endpoints under `/api/v1/ai-bom`. |
| AI BOM models | `apps/backend/api/models/ai_bom.py` | Defines AIBOM documents, components, risk levels, compliance status, and component metadata. |
| Automated evidence collector | `apps/backend/src/application/services/automated_evidence_collector.py` | Collects dataset quality, privacy, training bias, access controls, robustness, versioning, drift, fairness monitoring, audit logging, documentation, model card, and human oversight evidence. |
| Compliance mapper | `apps/backend/src/application/services/compliance_mapper.py` | Maps requirements to NIST AI RMF, EU AI Act, ISO 42001, OECD AI Principles, and local regulatory controls. |
| India-specific bias service | `apps/backend/src/application/services/india_bias_detection_service.py` | Computes fairness metrics for caste, religion, language, region, and intersectional groups. |
| Modern LLM bias service | `apps/backend/src/application/services/modern_llm_bias_service.py` | Runs WEAT, SEAT, minimal pairs, red-teaming, real-time monitoring, post-deployment auditing, and human-in-loop evaluation. |
| Benchmark suite service | `apps/backend/src/application/services/benchmark_suite_service.py` | Generates benchmark datasets with protected attributes and calculates fairness metrics. |
| Existing paper draft | `docs/paper/PAPER_DRAFT.md` | Already frames FairMind as unifying bias detection, compliance mapping, evidence collection, and AI BOM. |
| Fairness evidence profile generator | `apps/backend/src/application/services/fairness_evidence_profile_service.py` | Converts FairMind AIBOM, bias, evidence, remediation, and review records into the AIBOM fairness evidence profile schema. |

## Profile Crosswalk

| Profile field | FairMind source |
| --- | --- |
| `bom_ref`, component identity, upstream/downstream lineage | AI BOM service and AI BOM persisted components |
| `protected_attributes_tested` | India bias service, modern LLM bias service, benchmark suite service |
| `subgroup_coverage` | Benchmark suite protected attributes, India-specific subgroup tests, dataset service outputs collected as evidence |
| `fairness_metrics` | India bias service, benchmark suite service, comprehensive bias detection service |
| `bias_tests_run` | Modern LLM bias service, India bias service, comprehensive bias detection service |
| `known_bias_risks` | AI BOM risk assessment, bias service severity outputs, compliance mapper gaps |
| `remediation_history` | Compliance remediation service and report/evidence records when available |
| `validation_state` | Derived from source evidence state: missing, simulated, retrained, validated, or reviewed |
| `evidence_refs` | Automated evidence collector evidence keys, report IDs, test IDs, hashes, or dataset IDs |
| `evidence_freshness` | Evidence timestamps plus staleness rules for model updates, dataset refreshes, monitor changes, and report expiry |
| `review_status` | Human-in-loop evaluation output, release review status, or pending/manual review marker |
| `regulatory_mapping` | Compliance mapper controls and evidence requirements |
| `unknowns` | Any required profile field that cannot be supported by FairMind evidence should be explicit unknown risk |

## Correct Research Claim

FairMind is the prototype platform. The contribution is the fairness evidence profile that makes FairMind's existing AI BOM and evidence features reviewable for bias-risk governance.

Allowed claim:

> FairMind provides the system substrate for generating and evaluating AIBOM fairness evidence profiles.

Do not claim yet:

> FairMind has production-validated fairness evidence profiles.

## Implementation Path

1. Keep the current synthetic profiles as FairMind fixtures for schema validation and reviewer-task design.
2. Use `apps/backend/src/application/services/fairness_evidence_profile_service.py` as the minimal generator.
3. The generator accepts an AIBOM document, bias test outputs, evidence collector outputs, remediation records, and review status as mapping-shaped inputs.
4. The generator emits the schema in `schema/aibom_fairness_evidence.schema.json`.
5. Missing FairMind evidence becomes `unknowns`, not low risk.
6. Simulated FairMind evidence is labeled `simulated`, not `validated`.
