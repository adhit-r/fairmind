# Artifact README: AIBOM Fairness Evidence Research Package

## Package Purpose

This package is a reviewer-facing research artifact for evaluating an AIBOM fairness evidence profile. The profile is not a new BOM standard. It is a fairness evidence layer that can sit beside AI/ML BOM artifacts, including generic AI/ML BOMs and CycloneDX-style ML-BOMs, to make fairness evidence state easier to inspect.

The package is designed to support formative research on whether reviewers can identify missing, stale, simulated, unreviewed, or unsupported fairness evidence more reliably when that evidence state is explicit. It does not demonstrate that any represented system is fair, compliant, or production ready.

All example systems in this package are synthetic fixtures. They are useful for review tasks, validation checks, poster preparation, and paper planning, but they are not production evidence. Pilot results are pending until collected and recorded.

## Artifact Inventory

- `ARTIFACT_README.md`: Reviewer-facing package guide, inventory, validation quickstart, and reproducibility checklist.
- `schema/aibom_fairness_evidence.schema.json`: Draft 2020-12 JSON Schema for the fairness evidence profile.
- `examples/*_fairness_profile.json`: Synthetic fairness evidence profiles for loan approval, hiring ranker, and healthcare triage systems.
- `examples/generic_*_mlbom.json`: Generic AI/ML BOM baselines with component, version, and dependency information.
- `examples/cyclonedx_style_*_mlbom.json`: CycloneDX-style ML-BOM baselines with model-card-like fairness notes, but without the profile's explicit evidence-state and reviewer-action fields.
- `evaluation/fault_injection_cases.csv`: Fault cases for missing, stale, simulated, incomplete, or otherwise weak fairness evidence.
- `evaluation/reviewer_task_cards.md`: Reviewer tasks mapped to the synthetic systems and evidence gaps.
- `evaluation/study_protocol.md`: Formative pilot protocol for comparing review conditions.
- `evaluation/analysis_plan.md`: Analysis plan for detection, localization, false assurance, timing, confidence, and qualitative themes.
- `evaluation/response_sheet_template.csv`: Header-only pilot response sheet aligned to the protocol and analysis plan.
- `evaluation/validate_research_package.py`: Stdlib readiness check for required files, profile mappings, fault cases, baselines, and response-sheet columns.
- `evaluation/pilot_results.md`: Results template. It is intentionally empty until pilot data is collected.
- `evaluation/validation_notes.md`: Validation commands and cross-artifact consistency checks.
- `poster/poster_outline.md`: Poster structure and artifact narrative.
- `poster/soups_abstract.md`: Short abstract draft for poster-style presentation.
- `paper/CLAIM_LEDGER.md`: Current claim boundaries and support status.
- `paper/ROADMAP.md`: Paper development roadmap.
- `paper/draft.md`: Submission-oriented paper draft with pending-result markers kept explicit.
- `paper/prior_art_matrix.md`: Prior-art comparison matrix.
- `FAIRMIND_INTEGRATION.md`: Mapping between FairMind platform services and profile fields.
- `README.md`: Package-level overview.
- `AIBOM_FAIRNESS_EVIDENCE_PROFILE_PLAN.md`: Planning document for the profile and related research work.

## Quickstart Validation

Run validation from the repository root:

```bash
cd /Users/adhi/axonome/fairmind
```

Use the maintained commands in `evaluation/validation_notes.md` rather than copying long scripts into ad hoc notes:

```bash
sed -n '1,260p' research/aibom-fairness-evidence/evaluation/validation_notes.md
```

Run the stdlib package readiness check:

```bash
python3 research/aibom-fairness-evidence/evaluation/validate_research_package.py
```

At minimum, run the schema validation command from `evaluation/validation_notes.md`:

```bash
uvx --from check-jsonschema check-jsonschema \
  --schemafile research/aibom-fairness-evidence/schema/aibom_fairness_evidence.schema.json \
  research/aibom-fairness-evidence/examples/loan_approval_fairness_profile.json \
  research/aibom-fairness-evidence/examples/hiring_ranker_fairness_profile.json \
  research/aibom-fairness-evidence/examples/healthcare_triage_fairness_profile.json
```

Before a pilot, also run the cross-artifact and CycloneDX-style baseline checks documented in `evaluation/validation_notes.md`.

## Expected Outputs

Successful schema validation exits with status code `0` and no schema errors.

The cross-artifact consistency check in `evaluation/validation_notes.md` should print:

```text
validated FairMind context, component counts, and 24 fault-injection cases
```

The CycloneDX-style baseline consistency check should print:

```text
validated CycloneDX-style baseline mapping and profile-only field separation
```

If any command fails, treat the artifact package as not ready for pilot use until the failure is understood and fixed.

## Evidence-State Boundaries

The profile separates evidence state from fairness conclusions. Reviewers should treat states such as `current`, `stale`, `simulated`, `missing`, or `unreviewed` as signals about evidence quality and review action, not as automatic pass or fail outcomes.

Synthetic evidence is test data. It can support reviewer workflow evaluation, but it cannot support claims about a deployed model, real protected groups, real-world harms, or regulatory compliance.

The profile can make weak evidence easier to notice. It cannot prove that a model is fair, complete an audit by itself, replace domain review, or validate the correctness of underlying metrics.

## Running a Formative Pilot

1. Validate the package with the commands referenced in `evaluation/validation_notes.md`.
2. Select reviewer tasks from `evaluation/reviewer_task_cards.md`.
3. Assign artifact conditions from the generic AI/ML BOM, CycloneDX-style ML-BOM, and fairness evidence profile examples.
4. Ask reviewers to identify evidence gaps, affected components, likely reviewer actions, confidence, and review time.
5. Record observations in `evaluation/pilot_results.md`.
6. Analyze results using `evaluation/analysis_plan.md`.
7. Update `paper/CLAIM_LEDGER.md` only after data exists and only with claims supported by that data.

Until the pilot is complete, describe the study as planned or pending. Do not report detection rates, timing differences, confidence effects, or comparative reviewer performance as results.

## What Not To Claim

- Do not claim this package defines a new BOM standard.
- Do not claim the profile replaces CycloneDX, ML-BOMs, model cards, data cards, audits, or governance reports.
- Do not claim the synthetic examples are production evidence.
- Do not claim the profile proves a model is fair.
- Do not claim the pilot found reviewer improvements before pilot data is collected.
- Do not claim compliance with any regulation from these fixtures alone.
- Do not claim FairMind currently generates production-validated fairness evidence profiles from this package alone.

## File Map

```text
research/aibom-fairness-evidence/
  ARTIFACT_README.md
  README.md
  AIBOM_FAIRNESS_EVIDENCE_PROFILE_PLAN.md
  FAIRMIND_INTEGRATION.md
  schema/
    aibom_fairness_evidence.schema.json
  examples/
    *_fairness_profile.json
    generic_*_mlbom.json
    cyclonedx_style_*_mlbom.json
  evaluation/
    analysis_plan.md
    fault_injection_cases.csv
    pilot_results.md
    response_sheet_template.csv
    reviewer_task_cards.md
    study_protocol.md
    validate_research_package.py
    validation_notes.md
  paper/
    CLAIM_LEDGER.md
    ROADMAP.md
    draft.md
    prior_art_matrix.md
  poster/
    poster_outline.md
    soups_abstract.md
```

## Reproducibility Checklist

- Repository root is `/Users/adhi/axonome/fairmind`.
- The schema validates all three synthetic fairness profile examples.
- Fault-injection cases reference known synthetic systems and component IDs.
- Generic AI/ML BOM baselines are kept separate from profile-only evidence fields.
- CycloneDX-style baselines validate against the referenced CycloneDX schema and do not include profile-only evidence-state fields.
- Reviewer task cards map to the available synthetic systems.
- Pilot results remain blank or clearly marked pending until data is collected.
- Paper and poster claims match the support level recorded in `paper/CLAIM_LEDGER.md`.
- Synthetic examples are labeled and discussed as fixtures, not production evidence.
- Any publication or demo text states that the profile is layered onto AI/ML BOMs and is not a new BOM standard.
