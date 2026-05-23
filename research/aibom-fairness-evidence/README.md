# AIBOM Fairness Evidence Profile

## Thesis

AI bills of materials make model supply-chain components visible. A fairness evidence profile makes the status of fairness claims reviewable: which protected attributes were tested, which subgroups are missing, whether evidence is stale or simulated, what remediation was attempted, and whether a human reviewer accepted the claim.

This package does not define a new BOM standard. It defines a profile that FairMind can layer onto existing AI/ML BOM artifacts, including CycloneDX ML-BOM, model cards, data cards, and governance reports.

FairMind is the prototype platform for this work. The profile connects FairMind's AI BOM, bias detection, evidence collection, monitoring, and compliance mapping surfaces into a reviewer-facing evidence package. See `FAIRMIND_INTEGRATION.md` for the source-service crosswalk.

## Artifact Set

- `schema/aibom_fairness_evidence.schema.json`: JSON Schema for the fairness evidence profile.
- `FAIRMIND_INTEGRATION.md`: Mapping from FairMind services to fairness evidence profile fields.
- `examples/*_fairness_profile.json`: Three FairMind synthetic fixture profiles for loan approval, hiring, and healthcare triage systems.
- `examples/generic_*_mlbom.json`: Matching generic AI/ML BOM comparisons with component, version, and dependency metadata only.
- `evaluation/fault_injection_cases.csv`: Twenty-four evidence-gap cases for reviewer evaluation.
- `evaluation/reviewer_task_cards.md`: Twelve reviewer tasks mapped to the synthetic systems.
- `evaluation/pilot_results.md`: A formative pilot template for accuracy, time, confidence, and qualitative notes.
- `poster/soups_abstract.md`: SOUPS-ready abstract draft.
- `poster/poster_outline.md`: Poster structure, central figure, ethics, and limitations.

## Non-Goals

- Do not present this work as a competing BOM standard.
- Do not claim it replaces CycloneDX ML-BOM, model cards, data cards, or governance reports.
- Do not claim that the profile proves a system is fair.
- Do not claim FairMind currently produces production-validated fairness evidence profiles.
- Do not claim reviewer performance improvements unless a reviewed study has actually been run.

## Roadmap

1. **Research artifact package**: Complete the schema, FairMind integration map, examples, comparison artifacts, fault-injection cases, reviewer task cards, pilot template, poster abstract, and poster outline.
2. **Minimal generator**: Use `apps/backend/src/application/services/fairness_evidence_profile_service.py` to turn AIBOM documents, bias results, evidence records, remediation records, and review state into a profile JSON document.
3. **Reviewer UI**: Add a task-focused reviewer view with component graph, evidence-state badges, missing subgroup warnings, stale evidence warnings, remediation status, and JSON export.

## Validation

Run the validation command described in `evaluation/validation_notes.md` before using the package for a submission or pilot.
