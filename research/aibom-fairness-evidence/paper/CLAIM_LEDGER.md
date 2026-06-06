# Claim Ledger

This ledger controls what the AIBOM fairness evidence paper may claim. Use it before drafting, poster updates, talks, or submission materials.

## Paper Identity

Working title:

**Making Bias Evidence Reviewable in AI Bills of Materials**

Canonical framing:

> This work studies a fairness evidence profile layered onto AI and ML bills of materials. The profile makes the review status of fairness claims visible across components by exposing missing, stale, simulated, unsupported, and unreviewed evidence.

FairMind role:

> FairMind is the prototype system used to generate and surface the profile. It is not evidence that the profile is production-validated or that any deployed system is fair.

## Claim Status Labels

| Label | Meaning |
| --- | --- |
| `supported by artifact` | The schema, examples, generator, route, or UI implement the claim. |
| `supported by validation` | A fresh validation command verifies the claim. |
| `pilot required` | The claim requires reviewer data before use. |
| `future work` | The claim describes a planned extension, not current evidence. |
| `remove` | The claim is too broad, false, or not defensible. |

## Allowed Claims

| Claim | Status | Evidence | Required wording |
| --- | --- | --- | --- |
| The project defines a fairness evidence profile layered onto AI/ML BOM artifacts. | supported by artifact | `schema/aibom_fairness_evidence.schema.json`, `README.md` | "layered onto", not "new BOM standard" |
| The profile represents component lineage, fairness metrics, subgroup coverage, evidence freshness, validation state, review state, regulatory mapping, unknowns, and risk summary. | supported by artifact | schema required fields and synthetic examples | "represents" or "encodes", not "verifies" |
| Missing fairness evidence is represented as unknown risk, not low risk. | supported by artifact | `FairnessEvidenceProfileService._unknowns`, service tests | "unknown risk", not "safe" |
| Simulated evidence remains labeled as simulated. | supported by artifact | service tests and synthetic fixtures | "simulated", not "validated" |
| FairMind can generate a profile from AIBOM components and attached fairness evidence metadata. | supported by artifact | `fairness_evidence_profile_service.py`, route tests | "can generate from mapped inputs" |
| The synthetic examples and fault-injection cases support a formative reviewer evaluation. | supported by artifact | examples, `fault_injection_cases.csv`, `reviewer_task_cards.md` | "support evaluation design", not "prove improvement" |
| The current examples validate against the JSON Schema. | supported by validation | `evaluation/validation_notes.md` command | Use only after a fresh successful validation run. |

## Claims That Require Pilot Data

| Claim | Status | Evidence needed | Safe current wording |
| --- | --- | --- | --- |
| The profile improves reviewer detection of fairness evidence gaps. | pilot required | reviewer comparison against baseline BOM artifacts | "The study is designed to measure whether the profile improves detection." |
| The profile reduces false assurance. | pilot required | false assurance rate in generic/CycloneDX-style baseline versus profile condition | "False assurance is a target evaluation metric." |
| The profile improves component-level localization of fairness risks. | pilot required | component-localization accuracy in reviewer tasks | "The task set measures localization." |
| The profile reduces review time. | pilot required | timed reviewer tasks with counterbalanced artifacts | "Review time is measured." |
| Reviewers are better calibrated with the profile. | pilot required | confidence versus correctness analysis | "Confidence calibration is an analysis target." |

## Future-Work Claims

| Claim | Status | Safe wording |
| --- | --- | --- |
| The profile can be exported as CycloneDX extension metadata or OSCAL assessment evidence. | future work | "The profile is compatible with future mappings to CycloneDX extension metadata or OSCAL-style assessment evidence." |
| FairMind can support live production reviewer workflows. | future work | "FairMind is a prototype substrate for exploring reviewer workflows." |
| The profile can support continuous fairness assurance. | future work | "Continuous assurance is a future evaluation direction requiring live evidence feeds." |

## Claims To Remove

| Claim | Status | Reason |
| --- | --- | --- |
| This work defines a new AI BOM standard. | remove | The contribution is a profile layered onto existing BOMs. |
| FairMind proves that an AI system is fair. | remove | The profile exposes evidence state; it does not prove fairness. |
| FairMind has production-validated fairness evidence profiles. | remove | Current evidence is synthetic or prototype-level unless a production deployment is separately documented. |
| The reviewer study shows improvement before pilot data exists. | remove | No reviewer results should be claimed before a real pilot. |
| Generic AI/ML BOMs cannot contain fairness information. | remove | CycloneDX ML-BOM and model-card-style documentation can include fairness-relevant information. |
| This is the first system to connect fairness and AI BOMs. | remove | Too broad and likely false given CycloneDX ML-BOM and AIBOM assurance work. |

## Reviewer-Skeptic Objections

| Objection | Required answer |
| --- | --- |
| "Is this just Model Cards plus a BOM?" | The paper must show that the profile explicitly tracks evidence state, unknown risk, freshness, remediation validation, review status, and component-localized reviewer actions across the BOM graph. |
| "Is the baseline a strawman?" | Add CycloneDX-style baseline examples before running a serious evaluation. |
| "Where is the human evidence?" | Use formative wording until reviewer data exists. For full-paper claims, run the pilot. |
| "Does this prove fairness?" | No. It makes fairness evidence reviewable and exposes gaps. |
| "Why is this cybersecurity or governance-relevant?" | It turns fairness claims into auditable evidence states across an AI supply chain, reducing false assurance in governance review. |

## Current Evidence Inventory

| Artifact | Evidence state | Use in paper |
| --- | --- | --- |
| `schema/aibom_fairness_evidence.schema.json` | supported by artifact | Profile design and field definitions. |
| `examples/*_fairness_profile.json` | synthetic fixture | Demonstrates schema use and fault scenarios. |
| `examples/generic_*_mlbom.json` | weak baseline | Keep for simple comparison, but strengthen with CycloneDX-style baselines. |
| `evaluation/fault_injection_cases.csv` | synthetic benchmark seed | Supports reviewer task design. |
| `evaluation/reviewer_task_cards.md` | protocol seed | Needs full study protocol before pilot. |
| `evaluation/pilot_results.md` | template only | Do not cite as results. |
| `apps/backend/src/application/services/fairness_evidence_profile_service.py` | prototype implementation | Shows FairMind generator path. |
| `apps/backend/tests/test_fairness_evidence_profile_service.py` | prototype validation | Supports implementation claims only. |
| `apps/backend/tests/test_fairness_evidence_profile_route.py` | prototype validation | Supports route exposure claims only. |

## Drafting Rule

Every results sentence must point to one of these evidence states:

- synthetic artifact
- schema validation
- prototype route or service test
- formative pilot
- future work

If a sentence cannot be mapped, remove it or downgrade it.
